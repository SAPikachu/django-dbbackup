"""
Django Model to interact with dropbox.
  
Steps to Start using Dropbox Application:
  1. Setup an Application in your dropbox account.
  2. Create entries for the three required setting variables:
      * DROPBOX_CONSUMER_KEY
      * DROPBOX_CONSUMER_SECRET
      * DROPBOX_VERIFIER         (leave blank, dropbox not using it yet)
  3. You should only need to worry about calling the fucntion
     UserToken.get_access_token().  This will return an OAuthToken on
     success, and an AuthorizeUrl object on failure. The user will need
     to visit the URL and accept your Dropbox application.
     
For example usage, see: management/commands/pgbackup.py
"""
from django.contrib.auth.models import User
from django.db import models
from dropbox.auth import Authenticator
from dropbox.client import DropboxClient
from oauth.oauth import OAuthToken
from .config import CONFIG

REQUEST_TOKEN_KEY = 'request_token'
ACCESS_TOKEN_KEY = 'access_token'


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

class UserToken(models.Model):
    user  = models.ForeignKey(User, db_index=True)
    key   = models.CharField(max_length=255)
    token = models.CharField(max_length=255)
    
    class Meta:
        unique_together = (('user', 'key'),)
    
    def oauth(self):
        """ Return the oauth token. """
        return OAuthToken.from_string(self.token)
    
    @staticmethod
    def get_dropbox_client(user):
        """ Connect to dropbox and return a client object. """
        auth = Authenticator(CONFIG)
        accessToken = UserToken._get_access_token(user, auth)
        client = DropboxClient(CONFIG['server'], CONFIG['content_server'], CONFIG['port'], auth, accessToken.oauth())
        # Test the connection
        if (client.account_info().http_response.status != 200):
            accessToken.delete()
            UserToken.objects.get(user=user, key=REQUEST_TOKEN_KEY).delete()
            UserToken._create_request_token(user, Authenticator(CONFIG))
        return client
    
    @staticmethod
    def _get_access_token(user, auth):
        """ Return the Access OAuthToken for the specified user.  If the
            request token is not in the database, a new one will be created,
            saved to the database and a RequestUrl object will be returned.
        """
        try:
            return UserToken.objects.get(user=user, key=ACCESS_TOKEN_KEY)
        except UserToken.DoesNotExist:
            requestToken = UserToken._get_request_token(user, auth)
            return UserToken._create_access_token(user, auth, requestToken)
    
    @staticmethod
    def _get_request_token(user, auth):
        try:
            return UserToken.objects.get(user=user, key=REQUEST_TOKEN_KEY)
        except UserToken.DoesNotExist:
            return UserToken._create_request_token(user, auth)
    
    @staticmethod
    def _create_access_token(user, auth, requestToken):
        """ Create and save a access token for the specified user. """
        # Obtain the Access Token
        try:
            token = auth.obtain_access_token(requestToken.oauth(), CONFIG['verifier'])
        except AssertionError, e:
            if (" 403" in e.args[0]):
                requestToken.delete()
                UserToken._create_request_token(user, Authenticator(CONFIG))
        # Save it into the Database
        accessToken = UserToken()
        accessToken.user = user
        accessToken.key = ACCESS_TOKEN_KEY
        accessToken.token = token.to_string()
        accessToken.save()
        return accessToken
    
    @staticmethod
    def _create_request_token(user, auth):
        """ Create and save a request token for the specified user. """
        token = auth.obtain_request_token()
        requestToken = UserToken()
        requestToken.user = user
        requestToken.key = REQUEST_TOKEN_KEY
        requestToken.token = token.to_string()
        requestToken.save()
        # We know we're not authorized here
        raise DropboxNotAuthorized(auth.build_authorize_url(token))
    