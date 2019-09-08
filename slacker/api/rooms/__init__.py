import datetime as dt
import os

import requests_oauthlib
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from loguru import logger


class ApiLogin(Flow):
    """Helper class to interact with google apis in a more dev-friendly/slack-compatible way"""
    APP_TYPE = 'installed'
    AUTHORIZE_PROMPT = 'Please visit this URL to authorize the app: {url}'
    ENTER_CODE_MSG = 'Enter the authorization code: '

    @classmethod
    def from_secrets(cls, client_id, client_secret):
        scopes = ['https://www.googleapis.com/auth/calendar']
        oauth2session = requests_oauthlib.OAuth2Session(client_id=client_id, scope=scopes)
        redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        client_config = {
            cls.APP_TYPE: {
                "client_id": client_id,
                "client_secret": client_secret,
                "project_id": "quickstart-1565633779057",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [redirect_uri]
            }
        }
        return cls(oauth2session, cls.APP_TYPE, client_config,
                   redirect_uri=redirect_uri, code_verifier='abc123')

    def get_credentials_from_oauth2_flow(self):
        """Show authorization url to user and validate provided auth code to build api credentials.

        Oauth2 flow is as follows:
            1. App requests user consent providing an authorization url to visit
            2. User -hopefully- consents apps permissions and gets an auth code
            3. User enters the auth code into terminal prompt
            4. App exchanges auth code for api token that will be used on subsequent requests

        """
        print(self.AUTHORIZE_PROMPT.format(url=self.get_authorization_url()))
        code = input(self.ENTER_CODE_MSG)
        self.fetch_api_token(code=code)
        return self.credentials

    def get_authorization_url(self):
        """Return url that the user should follow to get an auth code"""
        # Set redirect uri that will be used on auth url
        auth_url, _state = self.authorization_url()
        return auth_url

    fetch_api_token = Flow.fetch_token

    @property
    def credentials(self):
        """Returns credentials from the OAuth 2.0 session.

        :meth:`fetch_token` must be called before accessing this. This method
        constructs a :class:`google.oauth2.credentials.Credentials` class using
        the session's token and the client config.

        Returns:
            google.oauth2.credentials.Credentials: The constructed credentials.

        Raises:
            ValueError: If there is no access token in the session.
        """
        return self.credentials_from_session(self.oauth2session, self.client_config)

    @staticmethod
    def credentials_from_session(session, client_config: dict):
        """Creates :class:`google.oauth2.credentials.Credentials` from a
        :class:`requests_oauthlib.OAuth2Session`.

        :meth:`fetch_token` must be called on the session before before calling
        this. This uses the session's auth token and the provided client
        configuration to create :class:`google.oauth2.credentials.Credentials`.
        This allows you to use the credentials from the session with Google
        API client libraries.

        Args:
            session (requests_oauthlib.OAuth2Session): The OAuth 2.0 session.
            client_config (Mapping[str, Any]): The subset of the client
                configuration to use. For example, if you have a web client
                you would pass in `client_config['web']`.

        Returns:
            google.oauth2.credentials.Credentials: The constructed credentials.

        Raises:
            ValueError: If there is no access token in the session.
        """
        if not session.token:
            raise ValueError('There is no access token for this session, did you call fetch_token?')

        credentials = Credentials(
            session.token['access_token'],
            refresh_token=session.token.get('refresh_token'),
            id_token=session.token.get('id_token'),
            token_uri=client_config.get('token_uri'),
            client_id=client_config.get('client_id'),
            client_secret=client_config.get('client_secret'),
            scopes=session.scope
        )
        credentials.expiry = dt.datetime.utcfromtimestamp(session.token['expires_at'])
        return credentials


calendar = ApiLogin.from_secrets(
    client_id=os.environ['CALENDAR_CLIENT'],
    client_secret=os.environ['CALENDAR_SECRET'],
)