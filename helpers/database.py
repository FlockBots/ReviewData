import sqlite3
from contextlib import closing
from datetime import datetime
from helpers import converters

class Database:
    def __init__(self, filename = 'data.db'):
        conn = sqlite3.connect(
            filename,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        self.connection = conn
        self.table = 'data'

    def create(self):
        with closing(self.connection.cursor()) as c:
            c.execute('''CREATE TABLE IF NOT EXISTS {} (
                id VARCHAR,
                comment_text VARCHAR,
                comment_author VARCHAR,
                submission_author VARCHAR,
                url VARCHAR,
                title VARCHAR,
                class INTEGER,
                analyzer VARCHAR,
                flag INTEGER,
                date timestamp
            )'''.format(self.table))
        self.connection.commit()

    def insert_comment(self, comment, doc_class=None, user=None):
        # text = remove_stopwords(comment.body)
        info = converters.comment_to_dict(comment)

        query = 'INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'.format(self.table)
        with closing(self.connection.cursor()) as c:
            c.execute(query, (
                info['id'],
                info['text'],
                info['author'].lower(),
                info['submission_author'].lower(),
                info['submission_url'],
                info['submission_title'],
                doc_class,
                user,
                doc_class is not None,
                datetime.now()
            ))
        self.connection.commit()

    def update_comment(self, comment, doc_class, user):
        submission = comment.submission
        text = remove_stopwords(comment.body)
        comment_author = str(comment.author).lower()
        submission_author = str(submission.author).lower()

        query = '''UPDATE {} SET 
            class = ?,
            analyzer = ?,
            flag = ?
            WHERE id = ?
            )'''.format(self.table)
        with closing(self.connection.cursor()) as c:
            c.execute(query, (doc_class, user, True, comment.id))
        self.connection.commit()

    def get_comment(self, comment):
        '''Gets the database entry associated with the praw Comment object'''
        query = 'SELECT * FROM {} WHERE id = ?'.format(self.table)
        with closing(self.connection.cursor()) as c:
            c.execute(query, (comment.id,))
            result = c.fetchone()
        if result:
            return converters.row_to_dict(result)
        return None