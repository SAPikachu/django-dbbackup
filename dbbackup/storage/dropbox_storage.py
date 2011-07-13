"""
Dropbox API Storage object.
"""
import tempfile, copy
from .base import BaseStorage, StorageError
from ConfigParser import ConfigParser
from django.conf import settings
from dropbox.auth import Authenticator
from dropbox.client import DropboxClient
from oauth.oauth import OAuthToken

DEFAULT_CONFIG = {
    'consumer_key': None,
    'consumer_secret': None,
    'verifier': '',
    'server': 'api.dropbox.com',
    'content_server': 'api-content.dropbox.com',
    'port': 80,
    'request_token_url': 'https://api.dropbox.com/0/oauth/request_token',
    'access_token_url': 'https://api.dropbox.com/0/oauth/access_token',
    'authorization_url': 'https://www.dropbox.com/0/oauth/authorize',
    'root': 'dropbox',
}


################################
#  Dropbox Storage Object
################################

class Storage(BaseStorage):
    """ Dropbox API Storage. """
    TOKENS_FILEPATH = getattr(settings, 'DBBACKUP_TOKENS_FILEPATH', None)
    DROPBOX_DIRECTORY = getattr(settings, 'DBBACKUP_DROPBOX_DIRECTORY', "/django-dbbackups/")
    DROPBOX_DIRECTORY = '/%s/' % DROPBOX_DIRECTORY.strip('/')
    DROPBOX_CONFIG = copy.copy(DEFAULT_CONFIG)
    DROPBOX_CONFIG.update(getattr(settings, 'DBBACKUP_DROPBOX_CONFIG', {}))
    REQUEST_KEY = 'request_key'
    ACCESS_KEY = 'access_key'
    _request_token = None
    _access_token = None

    def __init__(self, server_name=None):
        self._check_dropbox_errors()
        self.name = 'Dropbox'
        self.dropbox = self.get_dropbox_client()
        BaseStorage.__init__(self)

    def _check_dropbox_errors(self):
        """ Check we have all the required settings defined. """
        if not self.TOKENS_FILEPATH:
            raise StorageError('Dropbox storage requires DBBACKUP_TOKENS_FILEPATH to be defined in settings.')
        if not self.DROPBOX_CONFIG:
            raise StorageError('%s storage requires DBBACKUP_DROPBOX_CONFIG to be defined in settings.' % self.name)
        if not self.DROPBOX_CONFIG.get('consumer_key'):
            raise StorageError('%s storage requires DBBACKUP_DROPBOX_CONFIG["consumer_key"] to be specified.' % self.name)
        if not self.DROPBOX_CONFIG.get('consumer_secret'):
            raise StorageError('%s storage requires DBBACKUP_DROPBOX_CONFIG["consumer_secret"] to be specified.' % self.name)

    ###################################
    #  DBBackup Storage Methods
    ###################################

    def backup_dir(self):
        return self.DROPBOX_DIRECTORY

    def delete_file(self, filepath):
        """ Delete the specified filepath. """
        root = self.DROPBOX_CONFIG['root']
        response = self.dropbox.file_delete(root, filepath)
        self._check_response(response)

    def list_directory(self):
        """ List all stored backups for the specified. """
        root = self.DROPBOX_CONFIG['root']
        response = self.dropbox.metadata(root, self.DROPBOX_DIRECTORY)
        self._check_response(response)
        filepaths = [x['path'] for x in response.data['contents'] if not x['is_dir']]
        return sorted(filepaths)

    def write_file(self, filehandle):
        """ Write the specified file. """
        filehandle.seek(0)
        root = self.DROPBOX_CONFIG['root']
        response = self.dropbox.put_file(root, self.DROPBOX_DIRECTORY, filehandle)
        self._check_response(response)

    def read_file(self, filepath):
        """ Read the specified file and return it's handle. """
        root = self.DROPBOX_CONFIG['root']
        response = self.dropbox.get_file(root, filepath)
        self._check_response(response)
        filehandle = tempfile.SpooledTemporaryFile()
        filehandle.write(response.read())
        return filehandle

    def _check_response(self, response):
        """ Check we have a valid 200 response from Dropbox. """
        http_response = getattr(response, 'http_response', response)
        if http_response.status != 200:
            errmsg = "ERROR [%s]: %s" % (response.http_response.status, response.reason)
            raise StorageError(errmsg)

    ###################################
    #  oAuth Client Methods
    ###################################

    def get_dropbox_client(self):
        """ Connect and return a Dropbox client object. """
        self.read_token_file()
        auth = Authenticator(self.DROPBOX_CONFIG)
        access_token = self.get_access_token(auth)
        oauth = OAuthToken.from_string(access_token)
        server = self.DROPBOX_CONFIG['server']
        content_server = self.DROPBOX_CONFIG['content_server']
        port = self.DROPBOX_CONFIG['port']
        dropbox = DropboxClient(server, content_server, port, auth, oauth)
        # Test the connection
        if dropbox.account_info().http_response.status != 200:
            self.create_request_token(auth)
        return dropbox

    def read_token_file(self):
        """ Reload the config from disk. """
        tokenfile = ConfigParser()
        tokenfile.read(self.TOKENS_FILEPATH)
        if tokenfile.has_section(self.REQUEST_KEY) and tokenfile.has_option(self.REQUEST_KEY, 'token'):
            self._request_token = tokenfile.get(self.REQUEST_KEY, 'token')
        if tokenfile.has_section(self.ACCESS_KEY) and tokenfile.has_option(self.ACCESS_KEY, 'token'):
            self._access_token = tokenfile.get(self.ACCESS_KEY, 'token')

    def get_request_token(self, auth):
        """ Return Request oAuthToken. If not available, a new one will be created, saved
            and a RequestUrl object will be returned.
        """
        if not self._request_token:
            return self.create_request_token(auth)
        return self._request_token

    def get_access_token(self, auth):
        """ Return Access oAuthToken. If not available, a new one will be created and saved. """
        if not self._access_token:
            request_token = self.get_request_token(auth)
            return self.create_access_token(auth, request_token)
        return self._access_token

    def create_request_token(self, auth):
        """ Create and save a new request token. """
        self._request_token = auth.obtain_request_token()
        self._access_token = None
        self.save_token_file()
        # If we hit this code, we know were not authorized
        message = "Dropbox not authorized, visit the following URL to authorize:\n"
        message += auth.build_authorize_url(self._request_token)
        raise StorageError(message)

    def create_access_token(self, auth, request_token):
        """ Create and save a new access token to self.filepath. """
        try:
            oauth = OAuthToken.from_string(request_token)
            verifier = self.DROPBOX_CONFIG['verifier']
            self._access_token = auth.obtain_access_token(oauth, verifier).to_string()
            self.save_token_file()
            return self._access_token
        except AssertionError, e:
            # Check we have a bad request token
            if '403' in e.args[0]:
                self.create_request_token(Authenticator(self.config))

    def save_token_file(self):
        """ Save the config to disk. """
        tokenfile = ConfigParser()
        if self._request_token:
            tokenfile.add_section(self.REQUEST_KEY)
            tokenfile.set(self.REQUEST_KEY, 'token', self._request_token)
        if self._access_token:
            tokenfile.add_section(self.ACCESS_KEY)
            tokenfile.set(self.ACCESS_KEY, 'token', self._access_token)
        with open(self.TOKENS_FILEPATH, 'wb') as tokenhandle:
            tokenfile.write(tokenhandle)
