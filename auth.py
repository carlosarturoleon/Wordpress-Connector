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


def get_access_token(client_id, redirect_uri, client_secret, code):
    """
    Function to get an access token from WordPress.

    Args:
    client_id (str): Your application's client ID.
    redirect_uri (str): The redirect URI for your application.
    client_secret (str): Your application's client secret key.
    code (str): The code received from the authorization request.

    Returns:
    dict: A dictionary containing the access token and related information.
    """
    token_url = "https://public-api.wordpress.com/oauth2/token"
    data = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }

    response = requests.post(token_url, data=data)
    return response.json()
