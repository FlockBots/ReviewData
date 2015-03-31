def comment_to_dict(comment):
    submission = comment.submission
    return {
        'id': comment.id,
        'comment_text': comment.body,
        'comment_author': str(comment.author),
        'permalink': comment.permalink,
        'submission_author': str(submission.author),
        'url': submission.url,
        'title': submission.title
    }

def row_to_dict(row):
    return dict(zip(row.keys(), row))  