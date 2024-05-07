import requests, json
from flask import redirect, request


with open('credentials.json', 'r') as config_file:
    credentials = json.load(config_file)

CLIENT_ID = credentials['CLIENT_ID']
REDIRECT_URI = credentials['REDIRECT_URI']


def authorize():
    """
    Redirects the user to the WordPress authorization page.
    """
    auth_url = f"https://public-api.wordpress.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
    return redirect(auth_url)


def oauth_callback():
    """
    Handles the callback from WordPress OAuth.
    """
    code = request.args.get("code")
    if code:
        return f"Authorization code: {code}"
    else:
        return "No code provided by WordPress."

