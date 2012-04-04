"""
Restore pgdump files from Dropbox.
See __init__.py for a list of options.
"""
from ... import utils
from ...dbcommands import DBCommands
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
            self.dbcommands = DBCommands(self.database)
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
            filepaths = self.dbcommands.filter_filepaths(filepaths, self.servername)
            if not filepaths:
                raise CommandError("No backup files found in: %s" % self.storage.backup_dir())
            self.filepath = filepaths[-1]
        # Restore the specified filepath backup
        backupfile = self.storage.read_file(self.filepath)
        print "  Restore tempfile created: %s" % utils.handle_size(backupfile)
        self.dbcommands.run_restore_commands(backupfile)
