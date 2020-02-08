import datetime as dt
import os
import pickle

import requests_oauthlib
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from slacker.log import logger

from slacker.app_config import CALENDAR_CLIENT, CALENDAR_SECRET


class ApiLogin(Flow):
    """Helper class to interact with google apis in a more dev-friendly/slack-compatible way"""
    APP_TYPE = 'installed'
    AUTHORIZE_PROMPT = 'Please visit this URL to authorize the app: {url}'
    ENTER_CODE_MSG = 'Enter the authorization code: '
    CRED_FILE = 'calendar.pk'

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
        self.fetch_token(code=code)
        return self.credentials  # property that builds credentials from session api token and client secrets

    def get_authorization_url(self):
        """Return url that the user should follow to get an auth code"""
        # Set redirect uri that will be used on auth url
        auth_url, _state = self.authorization_url()
        return auth_url

    def get_token(self, **kwargs):
        """Fetch token, build credentials and save them into pickle file"""
        logger.debug('Fetching api token')
        tk = self.fetch_token(**kwargs)
        logger.debug(f'Api token: {tk}')
        creds = self.credentials
        logger.debug('Credentials built with api token')
        self.save_credentials(creds)
        logger.debug('Credentials stored.')

    @staticmethod
    def save_credentials(token):
        with open(ApiLogin.CRED_FILE, 'wb') as tk:
            pickle.dump(token, tk)

    @staticmethod
    def get_credentials():
        """Returns credentials from the OAuth 2.0 session.

        :meth:`fetch_token` must be called before accessing this. This method
        constructs a :class:`google.oauth2.credentials.Credentials` class using
        the session's token and the client config.

        Returns:
            google.oauth2.credentials.Credentials: The constructed credentials.

        Raises:
            ValueError: If there is no access token in the session.
        """
        # Load it from file it is saved
        if not os.path.exists(ApiLogin.CRED_FILE):
            raise ValueError('No credentials file found. Have you completed auth flow?')

        with open(ApiLogin.CRED_FILE, 'rb') as tk:
            creds = pickle.load(tk)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        return creds

    @property
    def credentials(self):
        """Just a wrapper property to give a friendly attribute name"""
        return self.credentials_from_session(self.oauth2session, self.client_config)

    @staticmethod
    def credentials_from_session(session, client_config: dict):
        """Copy pasted from superclass implementation to have it reachable and allow customization"""
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
    client_id=CALENDAR_CLIENT,
    client_secret=CALENDAR_SECRET,
)
