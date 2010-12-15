"""
Restore pgdump files from Dropbox.
See __init__.py for a list of options.
"""
import os
import sys
import subprocess
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import LabelCommand
from django.db import connection
from optparse import make_option
from ... import utils
from ...config import CONFIG
from ...models import UserToken
from ...models import DropboxNotAuthorized


class Command(LabelCommand):
    help  = "Restore pgdump files from Dropbox.\n"
    help += "Backup dir: %s" % CONFIG['backup_remote_dir']
    option_list = BaseCommand.option_list + (
        make_option("-d", "--database", help="Database key to backup"),
        make_option("-f", "--filename", help="Specifiec file to pull from Dropbox"),
        make_option("-s", "--servername", help="Use different servername's backup file"),
    )
    
    def handle(self, **options):
        """ Django command handler. """
        client = self._get_dropbox_client()
        if (options.get('servername') != None):
            CONFIG['backup_server_name'] = options['servername']
        # Get the Database settings to restore to
        databaseKey = options.get('database')
        if (not databaseKey):
            if (len(settings.DATABASES) >= 2):
                sys.exit("--database option is required for this project.")
            databaseKey = settings.DATABASES.keys()[0]
        database = settings.DATABASES[databaseKey]
        # Restore the database
        fileName = self._get_backup_filename(options, client, database)
        self._restore_backup(fileName, client, database)
        
    def _get_dropbox_client(self):
        """ Create and return a dropbox client. """
        try:
            print "Connecting to Dropbox"
            user = User.objects.get(username=CONFIG['backup_auth_username'])
            return UserToken.get_dropbox_client(user)
        except DropboxNotAuthorized, e:
            print "Account not Authorized."
            print "Please visit the following URL to active your account:"
            print e.url
            sys.exit(1)
            
    def _get_backup_filename(self, options, client, database):
        """ Return the dropbox backupPath to restore from. """
        if (options.get('filename')):
            fileName = options['filename']
        else:
            print "Finding latest backup"
            response = client.metadata(CONFIG['root'], CONFIG['backup_remote_dir'])
            assert response.http_response.status == 200
            backupPaths = utils.filter_backups(response.data['contents'], database)
            if (not backupPaths):
                sys.exit("No backups for database '%s' exist in: %s" % (database['NAME'], CONFIG['backup_remote_dir']))
            fileName = os.path.basename(sorted(backupPaths)[-1])
        print "  Restoring file: %s" % fileName
        return fileName
    
    def _restore_backup(self, fileName, client, database):
        """ Restore a backup file. """
        print "Restoring backup for database: %s" % database['NAME']
        dropboxFilePath = "%s%s" % (CONFIG['backup_remote_dir'], fileName)
        backupFilePath = "%s%s" % (CONFIG['backup_localwork_dir'], fileName)
        # Copy the backupFile from Dropbox
        print "  Pulling file from Dropbox: %s" % dropboxFilePath
        response = client.get_file(CONFIG['root'], dropboxFilePath)
        assert response.status == 200
        backupFile = open(backupFilePath, 'w')
        backupFile.write(response.read())
        backupFile.close()
        # Close, Drop & Restore the database
        connection.close()
        for command in utils.get_commands(database, backupFilePath, 'restore'):
            print "  Running: %s" % " ".join(command)
            utils.run_command(command)
    