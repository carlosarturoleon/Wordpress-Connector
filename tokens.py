import requests, json

with open('credentials.json', 'r') as config_file:
    credentials = json.load(config_file)

CLIENT_ID = credentials['CLIENT_ID']
REDIRECT_URI = credentials['REDIRECT_URI']
CLIENT_SECRET = credentials['CLIENT_SECRET']
CODE = credentials['CODE']


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


# Get Access Token
token = get_access_token(CLIENT_ID, REDIRECT_URI, CLIENT_SECRET, CODE)
print(token)