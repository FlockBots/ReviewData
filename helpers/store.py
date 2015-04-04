from redis import Redis
from threading import Thread
import config
import helpers
import praw

class CommentStore():
    def __init__(self, praw_instance=None):
        self.redis = Redis(config.settings['redis_host'])
        self.update_key = 'update'
        self.comment_key = 'comments'
        self.submission_key = 'submissions'
        self.set_key = 'comments_set'
        self.reddit = praw_instance or helpers.reddit.get_praw()

    def reset(self):
        self.redis.setbit(self.update_key, 0, 0)

    def get_comment_id(self):
        """
        Gets a comment ID from the store

        Returns:
            A string containing the ID
        """
        comment_id = self.redis.rpop(self.comment_key)
        self.redis.srem(self.set_key, comment_id)
        return comment_id

    def _add_comment_id(self, comment_id):
        """
        Adds a new comment to the store.

        Only adds the new comment if it's not already present

        Args:
            comment_id: (string) the ID of the comment.

        Returns:
            True: if added
            False: if it already exists
        """
        if self.redis.sadd(self.set_key, comment_id):
            self.redis.rpush(self.comment_key, comment_id)
            return True
        return False

    def update(self, n=100, threshold=50):
        """
        Adds new comment IDs the CommentStore

        Fetches new comments from Reddit and adds them to the local database and CommentStore.

        Args:
            n: (integer) Number of new comments to get.
            threshold: (integer) only perform update below this numbers
                        default: 50
        Returns:
            The number of comments in the store
        """

        db = helpers.Database()
        if self.redis.llen(self.comment_key) > threshold:
            return self.redis.llen(self.comment_key)

        # Only start updating if it's not being updated yet.
        if self.redis.setbit(self.update_key, 0, 1):
            return None

        # Add unclassified comments first
        for comment_id in db.get_unclassified_comments():
            self._add_comment_id(comment_id)

        # Add new comments from subreddits
        for subreddit in config.settings['subreddits']:
            self._update_comments(subreddit, n, db)

        # If there are still too little comments, add comments from archive
        while self.redis.llen(self.comment_key) < n and \
              self.redis.llen(self.submission_key):
            self._add_comments_from_archive()

        # Done updating, reset update bit
        self.redis.setbit(self.update_key, 0, 0)
        db.close()
        return self.redis.llen(self.comment_key)

    def _update_comments(self, subreddit, n, db):
        """
            Adds new comments from specified subreddit to the local database and CommentStore.

            Args:
                subreddit: (string) name of the subreddit to get comments from
                n: (integer) number of new comments to get
                db: helpers.Database instance
            Returns:
                None
        """
        comments = helpers.reddit.get_comments(self.reddit, subreddit)
        while n:
            try:
                comment = next(comments)
            except StopIteration:
                break

            db.insert_comment(comment)
            self._add_comment_id(comment.id)
            n -= 1

    def _add_comments_from_archive(self):
        """ Get comments from an archived submissions """

        # Create a redis list of submission IDs if it does not exist yet
        if not self.redis.exists(self.submission_key):
            self._add_submission_id_from_archive('archive.csv')

        # Get the next submission ID as a string
        submission_id = self.redis.lpop(self.submission_key).decode()
        submission = self.reddit.get_submission(submission_id=submission_id)
        submission.replace_more_comments(limit=None, threshold=0)
        comments = praw.helpers.flatten_tree(submission.comments)
        for comment in comments:
            self._add_comment_id(comment.id)

    def _add_submission_id_from_archive(self, filename):
        """ Download a new copy of the archive and add every submission to
            a redis list.

            Args:
                filename: (string) file to save the archive in
                          Default: 'archive.csv'
            Returns:
                None
            """
        # Temporarily set update bit to 0
        self.redis.setbit(self.update_key, 0, 0)
        archive_parser = helpers.Parser(filename)

        # Download a new archive
        archive_parser.download(key=config.api['archive_key'])
        for submission in archive_parser.get_submissions():
            self.redis.rpush(self.submission_key, submission.id)

        # Resume updating publicly
        self.redis.setbit(self.update_key, 0, 1)

    def next_comment(self, update_on_empty=True):
        """ Gets the next unparsed comment from the database.

        Args:
            update_on_empty: (bool) Whether to fetch new comments if the Redis list is empty.
                             default: True

        Returns:
            A sqlite.row object
        """
        comment_id = self.get_comment_id()
        comment = None
        if comment_id:
            db = helpers.Database()
            comment = db.get_comment_by_id(comment_id.decode())
            db.close()

        # If there are little comments available, start updating.
        if self.redis.llen(self.comment_key) < 10:
            update_thread = Thread(target=self.update)
            update_thread.start()

        return comment
