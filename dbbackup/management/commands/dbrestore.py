"""
Restore pgdump files from Dropbox.
See __init__.py for a list of options.
"""
from ... import utils
from ...commander import Commander
from ...storage.base import BaseStorage
from ...storage.base import StorageError
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from django.db import connection
from optparse import make_option


class Command(LabelCommand):
    help = "dbrestore [-d <dbname>] [-f <filename>] [-s <servername>]"
    option_list = BaseCommand.option_list + (
        make_option("-d", "--database", help="Database to restore"),
        make_option("-f", "--filepath", help="Specific file to backup from"),
        make_option("-s", "--servername", help="Use a different servername backup"),
    )

    def handle(self, **options):
        """ Django command handler. """
        try:
            connection.close()
            self.filepath = options.get('filepath')
            self.servername = options.get('servername')
            self.database = self._get_database(options)
            self.storage = BaseStorage.storage_factory()
            self.commander = Commander(self.database)
            self.restore_backup()
        except StorageError, err:
            raise CommandError(err)

    def _get_database(self, options):
        """ Get the database to restore. """
        database_key = options.get('database')
        if not database_key:
            if len(settings.DATABASES) >= 2:
                errmsg = "Because this project contains more than one database, you"
                errmsg += " must specify the --database option."
                raise CommandError(errmsg)
            database_key = settings.DATABASES.keys()[0]
        return settings.DATABASES[database_key]

    def restore_backup(self):
        """ Restore the specified database. """
        print "Restoring backup for database: %s" % self.database['NAME']
        # Fetch the latest backup if filepath not specified
        if not self.filepath:
            print "  Finding latest backup"
            filepaths = self.storage.list_directory()
            filepaths = self.commander.filter_filepaths(filepaths, self.servername)
            if not filepaths:
                raise CommandError("No backup files found in: %s" % self.storage.backup_dir())
            self.filepath = filepaths[-1]
        # Restore the specified filepath backup
        backupfile = self.storage.read_file(self.filepath)
        print "  Restore tempfile created: %s" % utils.handle_size(backupfile)
        self.commander.run_restore_commands(backupfile)



    #def handle(self, **options):
    #    """ Django command handler. """
    #    client = DropboxTokenFile.get_dropbox_client()
    #    if (options.get('servername') != None):
    #        CONFIG['backup_server_name'] = options['servername']
    #    # Get the Database settings to restore to
    #    databaseKey = options.get('database')
    #    if (not databaseKey):
    #        if (len(settings.DATABASES) >= 2):
    #
    #        databaseKey = settings.DATABASES.keys()[0]
    #    database = settings.DATABASES[databaseKey]
    #    # Restore the database
    #    print "Restoring backup for database: %s" % database['NAME']
    #    filename = options['filename'] or self.get_latest_filename(client, database)
    #    self.restore_backup(filename, client, database)
    #
    #def get_latest_filename(self, client, database):
    #    """ Return the latest filename in dropbox for backup. """
    #    print "  Finding latest backup"
    #    response = client.metadata(CONFIG['root'], CONFIG['backup_remote_dir'])
    #    assert response.http_response.status == 200
    #    backupPaths = utils.filter_backups(response.data['contents'], database)
    #    if (not backupPaths):
    #        sys.exit("No backups for '%s-%s' exist in: %s" % (database['NAME'],
    #            CONFIG['backup_server_name'], CONFIG['backup_remote_dir']))
    #    fileName = os.path.basename(sorted(backupPaths)[-1])
    #    return fileName
    #
    #def restore_backup(self, filename, client, database):
    #    """ Restore a backup file. """
    #    print "  Reading backup from Dropbox: %s" % filename
    #    dropboxFilepath = "%s%s" % (CONFIG['backup_remote_dir'], filename)
    #    response = client.get_file(CONFIG['root'], dropboxFilepath)
    #    assert response.status == 200
    #    restorefile = tempfile.SpooledTemporaryFile()
    #    restorefile.write(response.read())
    #    restorefile.seek(0, 2)
    #    print "  Restore tempfile created: %s" % utils.bytesToStr(restorefile.tell())
    #    print "  Closing database connection"
    #    connection.close()
    #    restorefile.seek(0)
    #    utils.run_restore_commands(database, restorefile)
