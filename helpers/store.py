from redis import Redis
from threading import Thread
import config
import helpers

class CommentStore():
    def __init__(self, praw_instance=None):
        self.redis = Redis(config.settings['redis_host'])
        self.update_key = 'update'
        self.comment_key = 'comments'
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

    def add_comment_id(self, comment_id):
        """
        Adds a new comment to the store.

        Only adds the new comment if it's not already present

        Args:
            comment_id: (string) the ID of the comment.

        Returns:
            None
        """
        if self.redis.sadd(self.set_key, comment_id):
            self.redis.rpush(self.comment_key, comment_id)

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
            self.add_comment_id(comment_id)

        # Add new comments from subreddits
        for subreddit in config.settings['subreddits']:
            self.update_comments(subreddit, n, db)

        # Done updating, reset update bit
        self.redis.setbit(self.update_key, 0, 0)
        db.close()
        return self.redis.llen(self.comment_key)

    def update_comments(self, subreddit, n, db):
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
            self.add_comment_id(comment.id)
            n -= 1

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
