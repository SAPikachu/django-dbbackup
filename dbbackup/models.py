"""
Django Model to interact with dropbox.

NOTE: This model is essentially a wrapper around a .ini file stored on disk.
  Because we are essentially wiping out any data in your database and replacing
  it new data from the backup, it wouldn't make sense to store the Dropbox
  UserTokens in there.
"""
from .config import CONFIG
from ConfigParser import ConfigParser
from dropbox.auth import Authenticator
from dropbox.client import DropboxClient
from oauth.oauth import OAuthToken

REQUEST_TOKEN_KEY = 'request'
ACCESS_TOKEN_KEY = 'access'


######################################
#  Request URL
######################################

class DropboxNotAuthorized(Exception):
    """ Stores the request URL. """
    def __init__(self, url):
        self.url = url


######################################
#  User Tokens
######################################

class DropboxTokenFile:
    """ Fetch and retrieve the Dropbox user key and token. """

    def __init__(self, filepath):
        self.filepath = filepath      # Where to save the tokens on disk
        self._request_token = None    # Request token (from tokenfile)
        self._access_token = None     # Access token (from tokenfile)
        self.read()                   # Read the tokenfile

    def get_dropbox_client(self):
        """ Connect and return a Dropbox client object. """
        auth = Authenticator(CONFIG)
        access_token = self.get_access_token(auth)
        oauth = OAuthToken.from_string(access_token)
        client = DropboxClient(CONFIG['server'], CONFIG['content_server'], CONFIG['port'], auth, oauth)
        # Test the connection
        if (client.account_info().http_response.status != 200):
            self.create_request_token(auth)
        return client

    def get_request_token(self, auth):
        """ Return the Request OAuthToken.  If the request token is not
            available, a new one will be created and saved to self.filepath
            and a RequestUrl object will be returned.
        """
        if (not self._request_token):
            return self.create_request_token(auth)
        return self._request_token

    def get_access_token(self, auth):
        """ Return the Access OAuthToken. If the access token is not
            available, a new one will be created and saved to self.filepath
            and a RequestUrl object will be returned.
        """
        if (not self._access_token):
            request_token = self.get_request_token(auth)
            return self.create_access_token(auth, request_token)
        return self._access_token

    def create_request_token(self, auth):
        """ Create and save a new request token to self.filepath. """
        self._request_token = auth.obtain_request_token()
        self._access_token = None
        self.save()
        # We know we're not authorized here
        raise DropboxNotAuthorized(auth.build_authorize_url(self._request_token))

    def create_access_token(self, auth, request_token):
        """ Create and save a new access token to self.filepath. """
        try:
            oauth = OAuthToken.from_string(request_token)
            self._access_token = auth.obtain_access_token(oauth, CONFIG['verifier']).to_string()
            self.save()
            return self._access_token
        except AssertionError, e:
            if (" 403" in e.args[0]):
                # Bad request token, remake it
                self.create_request_token(Authenticator(CONFIG))

    def read(self):
        """ Reload the config from disk. """
        config = ConfigParser()
        config.read(self.filepath)
        if (config.has_section(REQUEST_TOKEN_KEY)) and (config.has_option(REQUEST_TOKEN_KEY, 'token')):
            self._request_token = config.get(REQUEST_TOKEN_KEY, 'token')
        if (config.has_section(ACCESS_TOKEN_KEY)) and (config.has_option(ACCESS_TOKEN_KEY, 'token')):
            self._access_token = config.get(ACCESS_TOKEN_KEY, 'token')

    def save(self):
        """ Save the config to disk. """
        config = ConfigParser()
        if (self._request_token):
            config.add_section(REQUEST_TOKEN_KEY)
            config.set(REQUEST_TOKEN_KEY, 'token', self._request_token)
        if (self._access_token):
            config.add_section(ACCESS_TOKEN_KEY)
            config.set(ACCESS_TOKEN_KEY, 'token', self._access_token)
        with open(self.filepath, 'wb') as handle:
            config.write(handle)
