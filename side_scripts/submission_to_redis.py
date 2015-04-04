from redis import Redis
from praw import Reddit
from ArchiveParser import Parser

if __name__ == '__main__':
    redis = Redis()
    reddit = Reddit('Whisky Archive Parser by /u/FlockOnFire')
    archive_parser = Parser('archive.csv')

    counter = 0
    for submission in archive_parser.get_submissions(skip=2000):
        if counter % 500 == 0:
            print('{} submissions parsed'.format(counter))
        self.redis.rpush('submissions', submission.id)
        counter += 1