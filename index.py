from flask import Flask, session, request, redirect, abort, url_for, json
from config.keys import api
from config.keys import config
from helpers import reddit
from helpers.database import Database
from helpers.database import converters


app = Flask(__name__)
app.secret_key = config['app_secret']
praw_instance = reddit.get_praw()
comments = reddit.next_comment(praw_instance, 'scotch')
db = Database()
db.create()

@app.route('/')
def index():
    text = '<a href="%s">Authenticate with reddit</a>'
    return text % reddit.make_auth_url(session) 

@app.route(api['redirect_path'])
def reddit_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    if not state in session:
        # Uh-oh, this request wasn't started by us!
        abort(403)
    code = request.args.get('code')
    session['access_token'] = reddit.get_token(code)
    return redirect(url_for('classify'))

@app.route('/app/')
def classify():
    if not reddit.is_authorised(session):
        abort(403)
    return 'Welcome back, ' + session['username']

    # get data from server
    # 

@app.route('/test')
def test():
    pass

@app.route('/api/get_comment', methods=['POST'])
def api_get_comment():
    if not reddit.is_authorised(session):
        abort(403)
    return_data = {'status': 'ready'}
    global comments
    try:
        nxt = converters.comment_to_dict(next(comments))
    except StopIteration:
        comments = reddit.next_comment(praw_instance, 'scotch')
        try:
            nxt = converters.comment_to_dict(next(comments))
        except StopIteration:
            return_data['status'] = 'done'
            nxt = None
    return_data['comment'] = nxt
    return json.jsonify(return_data)

@app.route('/api/put_comment', methods=['POST'])
def api_put_comment():
    if not reddit.is_authorised(session):
        abort(403)
    else:
        return json.jsonify({'status': 'undefined'})
    # todo: unpack json data, verify and put in database


app.run(debug=True)