"""
S3 Storage object.
"""
import os, tempfile, sys
from .base import BaseStorage, StorageError
from django.conf import settings
from simples3.streaming import StreamingS3Bucket
from simples3.utils import aws_urlquote


################################
#  S3 Storage Object
################################

class Storage(BaseStorage):
    """ S3 API Storage. """
    S3_BUCKET = getattr(settings, 'DBBACKUP_S3_BUCKET', None)
    S3_ACCESS_KEY = getattr(settings, 'DBBACKUP_S3_ACCESS_KEY', None)
    S3_SECRET_KEY = getattr(settings, 'DBBACKUP_S3_SECRET_KEY', None)
    S3_DOMAIN = getattr(settings, 'DBBACKUP_S3_DOMAIN', 'https://s3.amazonaws.com/')
    S3_DIRECTORY =  getattr(settings, 'DBBACKUP_S3_DIRECTORY', "django-dbbackups/")
    S3_DIRECTORY = '%s/' % S3_DIRECTORY.strip('/')

    def __init__(self, server_name=None):
        self._check_filesystem_errors()
        self.name = 'AmazonS3'
        self.baseurl = self.S3_DOMAIN + aws_urlquote(self.S3_BUCKET)
        BaseStorage.__init__(self)

    def _check_filesystem_errors(self):
        """ Check we have all the required settings defined. """
        if not self.S3_BUCKET:
            raise StorageError('Filesystem storage requires DBBACKUP_S3_BUCKET to be defined in settings.')
        if not self.S3_ACCESS_KEY:
            raise StorageError('Filesystem storage requires DBBACKUP_S3_ACCESS_KEY to be defined in settings.')
        if not self.S3_SECRET_KEY:
            raise StorageError('Filesystem storage requires DBBACKUP_S3_SECRET_KEY to be defined in settings.')

    ###################################
    #  DBBackup Storage Methods
    ###################################

    @property
    def bucket(self):
        return StreamingS3Bucket(self.S3_BUCKET, self.S3_ACCESS_KEY,
                                 self.S3_SECRET_KEY, base_url=self.baseurl)

    def backup_dir(self):
        return self.S3_DIRECTORY

    def delete_file(self, filepath):
        """ Delete the specified filepath. """
        del self.bucket[filepath]

    def list_directory(self):
        """ List all stored backups for the specified. """
        return [x[0] for x in self.bucket.listdir(self.S3_DIRECTORY)]

    def write_file(self, filehandle):
        """ Write the specified file. """
        filepath = os.path.join(self.S3_DIRECTORY, filehandle.name)
        self.bucket.put_file(filepath, filehandle)

    def read_file(self, filepath):
        """ Read the specified file and return it's handle. """
        response = self.bucket.get(filepath)
        filehandle = tempfile.SpooledTemporaryFile()
        filehandle.write(response.read())
        return filehandle
