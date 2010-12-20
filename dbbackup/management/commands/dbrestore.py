"""
Restore pgdump files from Dropbox.
See __init__.py for a list of options.
"""
import os
import sys
import tempfile
from ... import utils
from ...config import CONFIG
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import LabelCommand
from django.db import connection
from optparse import make_option


class Command(LabelCommand):
    help = "Restore pgdump files from Dropbox.\n"
    help += "Backup dir: %s" % CONFIG['backup_remote_dir']
    option_list = BaseCommand.option_list + (
        make_option("-d", "--database", help="Database key to backup"),
        make_option("-f", "--filename", help="Specifiec file to pull from Dropbox"),
        make_option("-s", "--servername", help="Use different servername's backup file"),
    )

    def handle(self, **options):
        """ Django command handler. """
        client = utils.get_dropbox_client()
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
        print "Restoring backup for database: %s" % database['NAME']
        filename = options['filename'] or self.get_latest_filename(client, database)
        self.restore_backup(filename, client, database)

    def get_latest_filename(self, client, database):
        """ Return the latest filename in dropbox for backup. """
        print "  Finding latest backup"
        response = client.metadata(CONFIG['root'], CONFIG['backup_remote_dir'])
        assert response.http_response.status == 200
        backupPaths = utils.filter_backups(response.data['contents'], database)
        if (not backupPaths):
            sys.exit("No backups for '%s-%s' exist in: %s" % (database['NAME'],
                CONFIG['backup_server_name'], CONFIG['backup_remote_dir']))
        fileName = os.path.basename(sorted(backupPaths)[-1])
        return fileName

    def restore_backup(self, filename, client, database):
        """ Restore a backup file. """
        print "  Reading backup from Dropbox: %s" % filename
        dropboxFilepath = "%s%s" % (CONFIG['backup_remote_dir'], filename)
        response = client.get_file(CONFIG['root'], dropboxFilepath)
        assert response.status == 200
        restorefile = tempfile.SpooledTemporaryFile()
        restorefile.write(response.read())
        restorefile.seek(0, 2)
        print "  Restore tempfile created: %s" % utils.bytesToStr(restorefile.tell())
        print "  Closing database connection"
        connection.close()
        restorefile.seek(0)
        utils.run_restore_commands(database, restorefile)
