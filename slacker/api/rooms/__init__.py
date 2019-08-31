import os

from google_auth_oauthlib.flow import InstalledAppFlow as GoogleOAuth2


class ApiLogin(GoogleOAuth2):
    """Class to interact with google apis through slack"""

    @classmethod
    def from_secrets(cls, client_id, client_secret, project_id):
        config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "project_id": 'quickstart-1565633779057' or project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                "scopes": ['https://www.googleapis.com/auth/calendar'],
            }
        }
        return GoogleOAuth2.from_client_config(config, scopes=config.pop('scopes'))

    def get_authorization_url(self):
        """Return url that the user should follow to get an auth code"""
        # Set uri for authorization that will be used to build auth url
        self.redirect_uri = self._OOB_REDIRECT_URI
        auth_url, _ = self.authorization_url()
        return auth_url

    def set_token(self, auth_code):
        """Sets a token for api calls using the auth_code generated on user consent"""
        # Fetch token and save it as self.token instance attribute
        self.fetch_token(code=auth_code)

        # Build credentials from session token and client secrets
        creds = self.credentials

        return creds


CalendarApi = ApiLogin.from_secrets(
    client_id=os.getenv('CALENDAR_CLIENT_ID'),
    client_secret=os.getenv('CALENDAR_CLIENT_SECRET'),
    project_id=os.getenv('CALENDAR_PROJECT_NAME', 'Missing Project name'),
)
