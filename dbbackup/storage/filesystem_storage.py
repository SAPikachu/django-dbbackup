"""
Filesystem Storage object.
"""
import os, tempfile
from .base import BaseStorage, StorageError
from django.conf import settings


################################
#  Dropbox Storage Object
################################

class Storage(BaseStorage):
    """ Dropbox API Storage. """
    BACKUP_DIRECTORY = getattr(settings, 'DBBACKUP_FILESYSTEM_DIRECTORY', None)

    def __init__(self, server_name=None):
        self._check_filesystem_errors()
        self.name = 'Filesystem'
        BaseStorage.__init__(self)

    def _check_filesystem_errors(self):
        """ Check we have all the required settings defined. """
        if not self.BACKUP_DIRECTORY:
            raise StorageError('Filesystem storage requires DBBACKUP_FILESYSTEM_DIRECTORY to be defined in settings.')

    ###################################
    #  DBBackup Storage Methods
    ###################################

    def backup_dir(self):
        return self.BACKUP_DIRECTORY

    def delete_file(self, filepath):
        """ Delete the specified filepath. """
        os.unlink(filepath)

    def list_directory(self):
        """ List all stored backups for the specified. """
        filepaths = os.listdir(self.BACKUP_DIRECTORY)
        filepaths = [os.path.join(self.BACKUP_DIRECTORY, path) for path in filepaths]
        return sorted(filter(os.path.isfile, filepaths))

    def write_file(self, filehandle):
        """ Write the specified file. """
        filehandle.seek(0)
        backuppath = os.path.join(self.BACKUP_DIRECTORY, filehandle.name)
        backupfile = open(backuppath, 'w')
        data = filehandle.read(1024)
        while data:
            backupfile.write(data)
            data = filehandle.read(1024)
        backupfile.close()

    def read_file(self, filepath):
        """ Read the specified file and return it's handle. """
        return open(filepath, 'r')
