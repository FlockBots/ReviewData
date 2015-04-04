from flask import Flask, session, request, redirect, abort, url_for, json, render_template
import helpers
import config
import requests
from flask import Markup
from markdown import markdown

app = Flask(__name__)

@app.route('/')
def index():
    if not helpers.reddit.is_authorised(session):
        auth_url = helpers.reddit.make_auth_url(session) 
        return render_template('index.html', auth_url=auth_url)
    return render_template('index.html', name=session['username'])

@app.route('/403')
@app.errorhandler(403)
def forbidden(e=None):
    auth_url = helpers.reddit.make_auth_url(session) 
    return render_template('403.html', auth_url=auth_url)

@app.route(config.api['redirect_path'])
def reddit_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not state in session:
        # Uh-oh, this request wasn't started by us!
        abort(403)
    code = request.args.get('code')
    session['access_token'] = helpers.reddit.get_token(code)
    return redirect(url_for('classify'))

@app.route('/logout')
def logout():
    session.pop('access_token')
    session.pop('username')
    return redirect(url_for('index'))

@app.route('/app/')
def classify():
    if not helpers.reddit.is_authorised(session):
        abort(403)

    db = helpers.Database()
    number_reviews, number_total = db.get_stats(session['username'])
    return render_template('classify.html', name=session['username'], numbers={'reviews': number_reviews, number_total})

@app.route('/api/get_comment')
def api_get_comment():
    if not helpers.reddit.is_authorised(session):
        abort(403)
    store = helpers.CommentStore()
    comment = store.next_comment()
    data = {}
    if not comment:
        data['status'] = 'updating'
    else:
        comment['comment_text'] = Markup(markdown(comment['comment_text']))
        data['status'] = 'ready'
        data['comment'] = comment
    return json.jsonify(data)

@app.route('/api/put_comment', methods=['POST'])
def api_put_comment():
    if not helpers.reddit.is_authorised(session):
        abort(403)
    if 'application/json' not in request.headers['Content-Type'].lower():
        abort(415)
    db = helpers.Database()
    db_comment = db.get_comment_by_id(request.json['comment_id'])
    if db_comment and not db_comment['class']:
        db.update_comment(request.json['comment_id'],
            request.json['doc_class'],
            session['username'])
    db.close()
    return json.jsonify({'status': 'ready'})

def reset():
    store = helpers.CommentStore()
    store.reset()

if __name__ == '__main__':
    reset()
    app.secret_key = config.settings['app_secret']
    praw_instance = helpers.reddit.get_praw()
    db = helpers.Database()
    db.create()
    db.close()
    app.run(host=config.settings['host'], port=config.settings['port'])
