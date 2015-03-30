from flask import Flask, session, request, redirect, abort, url_for, json
import helpers
import config
import requests

app = Flask(__name__)

@app.route('/')
def index():
    text = '<a href="%s">Authenticate with reddit</a>'
    return text % helpers.reddit.make_auth_url(session) 

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

@app.route('/app/')
def classify():
    if not helpers.reddit.is_authorised(session):
        abort(403)
    length = helpers.store.update()
    return 'Welcome back, ' + session['username']

    # get data from server
    # 

@app.route('/api/get_comment', methods=['POST'])
def api_get_comment():
    if not helpers.reddit.is_authorised(session):
        abort(403)
    return_data = {'status': 'ready'}
    
    return json.jsonify(return_data)

@app.route('/api/put_comment', methods=['POST'])
def api_put_comment():
    if not helpers.reddit.is_authorised(session):
        abort(403)
    print(request.headers['Content-Type'])
    if 'application/json' not in request.headers['Content-Type'].lower():
        abort(415)
    print(request.json['comment'])
    db = Database()
    db.update_comment(request.json['comment_id'], request.json['class'], request.json['user'])
    return json.jsonify({'status': 'undefined'})
    # todo: verify data (e.g. try/except) proper return status


if __name__ == '__main__':
    app.secret_key = config.settings['app_secret']
    praw_instance = helpers.reddit.get_praw()
    db = helpers.Database()
    db.create()
    app.run(debug=True)