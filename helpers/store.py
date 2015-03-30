from redis import Redis
from config import keys
from helpers import reddit

class CommentStore():
    def __init__(self, praw_instance=None):
        self.redis = Redis(keys.config['redis_host'])
        self.update_key = 'update'
        self.comment_key = 'comments'
        self.reddit = praw_instance or reddit.get_praw()
        self.db = Database()

    def is_updating(self):
        return self.redis.getbit(self.update_key, 0)

    def update(self, n=100):
        """
        Adds new comment IDs the CommentStore

        Fetches new comments from Reddit and adds them to the local database and CommentStore.

        Args:
            n: (integer) Number of new comments to get. 
        """
        if self.redis.setbit(self.update_key, 0, 1):
            return 0

        for subreddit in keys.config['subreddits']:
            self.update_comments(subreddit, n)

        return self.redis.llen(self.comment_key)

    def update_comments(self, subreddit, n):
        """
            Adds new comments from specified subreddit to the local database and CommentStore.

            Args:
                subreddit: (string) name of the subreddit to get comments from
                n: (integer) number of new comments to get
        """
        size = 0
        comments = reddit.get_comments(self.reddit, subreddit)
        while n:
            try:
                comment = next(comments)
            except StopIteration:
                break

            self.db.insert_comment(comment)
            n -= 1