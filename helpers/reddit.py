from config.keys import flockbot
from config.keys import api
from config.keys import config
import praw
import requests
import requests.auth
import urllib.parse
from uuid import uuid4
from helpers.database import Database
from helpers import converters
from datetime import datetime


'''
PRAW helper functions
'''
def get_praw():
    reddit = praw.Reddit('User-Agent: {}'.format({'User-Agent': config['user-agent']}))
    reddit.login(flockbot['username'], flockbot['password'])
    return reddit

def next_comment(praw_instance, subreddit, n=5):
    if not praw_instance:
        praw_instance = get_praw()
    # Get the latest comments on Reddit
    # If it's in the database
    #   - if it's not analyzed and old enough, grab it anyway
    #   - otherwise, grab a new one

    db = Database()
    comments = praw_instance.get_comments(subreddit, limit=1000)
    for comment in comments:
        if len(comment.body) < 150:
            continue

        row = db.get_comment(comment)
        if row:
            delta = datetime.now() - row['date']
            if row['class'] or delta.seconds // 10 * 60 < 1:
                continue
        else:
            db.insert_comment(comment)
        yield comment
'''
Reddit API Authorization
'''
# Authorization process as layed out in https://gist.github.com/kemitche/9749639
def make_auth_url(session):
    '''Create an authorization url for permanent identity access'''
    state = str(uuid4())
    session[state] = True
    params = {
        'client_id': api['client_id'],
        'response_type': 'code',
        'state': state,
        'redirect_uri': config['base_url'] + api['redirect_path'],
        'duration': 'temporary',
        'scope': 'identity'
    }
    url = api['base_auth_url'] + urllib.parse.urlencode(params)
    return url

def get_token(code):
    client_auth = requests.auth.HTTPBasicAuth(api['client_id'], api['client_secret'])
    post_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config['base_url'] + api['redirect_path']
    }
    headers = {'User-Agent': config['user-agent']}
    response = requests.post(
        api['access_code_url'],
        auth = client_auth,
        headers = headers,
        data = post_data
    )
    token_json = response.json()
    return token_json['access_token'] 

def get_username(access_token):
    headers = {'User-Agent': config['user-agent']}
    headers.update({ 'Authorization': 'bearer ' + access_token })
    response = requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)
    me_json = response.json()
    try:
        return me_json['name']
    except KeyError:
        return ''

def is_authorised(session):
    if not 'access_token' in session:
        return False
    username = get_username(session['access_token'])
    if not username.lower() in config['allowed']:
        return False
    session['username'] = username
    return True