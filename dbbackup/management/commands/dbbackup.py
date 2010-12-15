"""
Save backup files to Dropbox.
"""
import datetime
import re
import tempfile
from ... import utils
from ...config import CONFIG
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import LabelCommand
from optparse import make_option


class Command(LabelCommand):
    help = "Save pgdump files to Dropbox.\n"
    help += "Backup dir: %s" % CONFIG['backup_remote_dir']
    option_list = BaseCommand.option_list + (
        make_option("-c", "--clean", help="Clean up old backup files", action="store_true", default=False),
        make_option("-d", "--database", help="Database key to backup (defaults to all)"),
        make_option("-s", "--servername", help="Specifiy a servername to append to the filename"),
    )

    def handle(self, **options):
        """ Django command handler. """
        client = utils.get_dropbox_client()
        if (options.get('servername') != None):
            CONFIG['backup_server_name'] = options['servername']
        databaseKeys = CONFIG['backup_databases']
        if (options.get('database')):
            databaseKeys = [options['database']]
        for databaseKey in databaseKeys:
            database = settings.DATABASES[databaseKey]
            self.save_new_backup(client, database)
            if (options['clean']):
                self.cleanup_old_backups(client, database)

    def save_new_backup(self, client, database):
        """ Save a new backup file. """
        print "Backing up database: %s" % database['NAME']
        backupfile = tempfile.SpooledTemporaryFile()
        backupfile.name = utils.backup_filename(database)
        utils.run_backup_commands(database, backupfile)
        backupfile.seek(0, 2)
        print "  Backup tempfile created: %s" % utils.bytesToStr(backupfile.tell())
        print "  Saving backup to Dropbox: %s" % backupfile.name
        backupfile.seek(0)
        response = client.put_file(CONFIG['root'], CONFIG['backup_remote_dir'], backupfile)
        assert response.http_response.status == 200

    def cleanup_old_backups(self, client, database):
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
