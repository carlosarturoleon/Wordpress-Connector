from auth import authorize, oauth_callback

def configure_routes(app):
    @app.route("/authorize")
    def authorize_route():
        """
        Redirects the user to the WordPress authorization page.
        """
        return authorize()

    @app.route("/oauth")
    def oauth_callback_route():
        """
        Handles the callback from WordPress OAuth.
        This route gets the code from the request and processes it to obtain an access token.
        """
        return oauth_callback()
