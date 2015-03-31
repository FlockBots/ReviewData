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
                id VARCHAR PRIMARY KEY,
                comment_text VARCHAR NOT NULL,
                comment_author VARCHAR NOT NULL,
                submission_author VARCHAR NOT NULL,
                permalink VARCHAR NOT NULL,
                url VARCHAR,
                title VARCHAR NOT NULL,
                class INTEGER,
                user VARCHAR
            )'''.format(self.table))
        self.connection.commit()

    def insert_comment(self, comment, doc_class=None, user=None):
        # text = remove_stopwords(comment.body)
        info = converters.comment_to_dict(comment)

        query = 'INSERT INTO {} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'.format(self.table)
        with closing(self.connection.cursor()) as c:
            c.execute(query, (
                info['id'],
                info['comment_text'],
                info['comment_author'].lower(),
                info['submission_author'].lower(),
                info['permalink'],
                info['url'],
                info['title'],
                doc_class,
                user
            ))
        self.connection.commit()

    def update_comment(self, comment_id, doc_class, user):
        query = '''UPDATE {} SET 
            class = ?,
            user = ?
            WHERE id = ?
            '''.format(self.table)
        with closing(self.connection.cursor()) as c:
            c.execute(query, (doc_class, user, comment_id))
        self.connection.commit()

    def get_comment_by_id(self, comment_id):
        '''Gets the database entry where id equals comment_id.

        Args:
            comment_id: Reddit ID of the comment
        Returns:
            Dictionary of the comment's attributes
        '''
        query = 'SELECT * FROM {} WHERE id = ?'.format(self.table)
        with closing(self.connection.cursor()) as c:
            c.execute(query, (comment_id,))
            result = c.fetchone()
        if result:
            return converters.row_to_dict(result)
        return None

    def get_unclassified_comments(self):
        '''Gets unclassified comments

        Returns:
            A list of comment IDs from unclassified comments
        '''
        query = 'SELECT id FROM {} WHERE class is null OR user is null'.format(self.table)
        with closing(self.connection.cursor()) as c:
            rows = c.execute(query)
            results = [row['id'] for row in rows]
        return results
