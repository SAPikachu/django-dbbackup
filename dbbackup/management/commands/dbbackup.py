"""
Save pgdump files to Dropbox.
See __init__.py for a list of options.
"""
import os
import re
import sys
import glob
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import LabelCommand
from optparse import make_option
from ... import utils
from ...config import CONFIG
from ...models import UserToken
from ...models import DropboxNotAuthorized


class Command(LabelCommand):
    help  = "Save pgdump files to Dropbox.\n"
    help += "Backup dir: %s" % CONFIG['backup_remote_dir']
    option_list = BaseCommand.option_list + (
        make_option("-c", "--clean", help="Clean up old backup files", action="store_true", default=False),
        make_option("-d", "--database", help="Database key to backup (defaults to all)"),
        make_option("-s", "--servername", help="Specifiy a servername to append to the filename"),
    )
    
    def handle(self, **options):
        """ Django command handler. """
        client = self._get_dropbox_client()
        if (options.get('servername') != None):
            CONFIG['backup_server_name'] = options['servername']
        databaseKeys = CONFIG['backup_databases']
        if (options.get('database')):
            databaseKeys = [options['database']]
        for databaseKey in databaseKeys:
            database = settings.DATABASES[databaseKey]
            self._save_new_backup(client, database)
            if (options['clean']):
                self._cleanup_old_backups(client, database)
        
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
        
    def _save_new_backup(self, client, database):
        """ Save a new backup file. """
        print "Saving backup for database: %s" % database['NAME']
        fileName = utils.backup_filename(database)
        # Create the local temp backup file
        backupFilePath = "%s%s" % (CONFIG['backup_localwork_dir'], fileName)
        for command in utils.get_commands(database, backupFilePath, 'backup'):
            print " ".join(command)
            utils.run_command(command)
        # Copy the backupFile to Dropbox
        dropboxFilePath = "%s%s" % (CONFIG['backup_remote_dir'], fileName)
        print "  Pushing file to Dropbox: %s" % dropboxFilePath
        backupFile = open(backupFilePath, 'r')
        response = client.put_file(CONFIG['root'], CONFIG['backup_remote_dir'], backupFile)
        backupFile.close()
        assert response.http_response.status == 200
        # Cleanup the working directory
        print "  Cleaning working directory"
        fileMatch = utils.backup_filename_match(database)
        workingFilePaths = glob.glob("%s%s*" % (CONFIG['backup_localwork_dir'], fileMatch))
        for filePath in workingFilePaths:
            os.unlink(filePath)
        
    def _cleanup_old_backups(self, client, database):
        """ Cleanup old backups.  Delete everything but the last 10
            backups, and any backup that occur on first of the month.
        """
        print "Cleaning old backups"
        response = client.metadata(CONFIG['root'], CONFIG['backup_remote_dir'])
        assert response.http_response.status == 200
        backupPaths = utils.filter_backups(response.data['contents'], database)
        for backupPath in sorted(backupPaths[0:-10]):
            fileMatch = utils.backup_filename_match(database, '(.*?)')
            dateMatch = re.findall(fileMatch, backupPath)[0]
            dateTime = datetime.datetime.strptime(dateMatch, CONFIG['backup_date_format'])
            dayOfMonth = int(dateTime.strftime("%d"))
            if (dayOfMonth != 1):
                print "  Deleting %s" % backupPath
                response = client.file_delete(CONFIG['root'], backupPath)
                assert response.http_response.status == 200
    
    