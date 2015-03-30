def comment_to_dict(comment):
    submission = comment.submission
    return {
        'id': comment.id,
        'text': comment.body,
        'author': str(comment.author),
        'permalink': comment.permalink,
        'submission_author': str(submission.author),
        'url': submission.url,
        'submission_title': submission.title
    }

def row_to_dict(row):
    return dict(zip(row.keys(), row))  