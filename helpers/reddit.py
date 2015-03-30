import config
import praw
import requests
import requests.auth
import urllib.parse
from uuid import uuid4
import helpers
from datetime import datetime

'''
PRAW helper functions
'''
def get_praw():
    reddit_praw = praw.Reddit('User-Agent: {}'.format({'User-Agent': config.settings['user-agent']}))
    reddit_praw.login(config.flockbot['username'], config.flockbot['password'])
    return reddit_praw

def get_comments(praw_instance, subreddit):
    """ Gets unparsed comments from Reddit and sets them up in a Redis list.

    Args:
        praw_instance: The instance of the reddit API wrapper 
        subreddit: (string) The name of the subreddit to fetch comments from
        n: (int) the maximum number of comments to fetch.

    Returns:
        A generator of praw.Comment objects that do not occur in the local database yet.
    """
    db = helpers.Database()
    comments = praw_instance.get_comments(subreddit, limit=None)
    for comment in comments:
        if len(comment.body) < 150:
            continue

        if not db.get_comment_by_id(comment.id):
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
        'client_id': config.api['client_id'],
        'response_type': 'code',
        'state': state,
        'redirect_uri': config.settings['base_url'] + config.api['redirect_path'],
        'duration': 'temporary',
        'scope': 'identity'
    }
    url = config.api['base_auth_url'] + urllib.parse.urlencode(params)
    return url

def get_token(code):
    client_auth = requests.auth.HTTPBasicAuth(config.api['client_id'], config.api['client_secret'])
    post_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config.settings['base_url'] + config.api['redirect_path']
    }
    headers = {'User-Agent': config.settings['user-agent']}
    response = requests.post(
        config.api['access_code_url'],
        auth = client_auth,
        headers = headers,
        data = post_data
    )
    token_json = response.json()
    return token_json['access_token'] 

def get_username(access_token):
    headers = {'User-Agent': config.settings['user-agent']}
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
    if not username.lower() in config.settings['allowed']:
        return False
    session['username'] = username
    return True