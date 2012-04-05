"""
Process the Backup or Restore commands.
"""
import copy, os, re, shlex
from datetime import datetime
from django.conf import settings
from django.core.management.base import CommandError
from subprocess import Popen


READ_FILE = '<READ_FILE>'
WRITE_FILE = '<WRITE_FILE>'
DATE_FORMAT = getattr(settings, 'DBBACKUP_DATE_FORMAT', '%Y-%m-%d-%H%M%S')
SERVER_NAME = getattr(settings, 'DBBACKUP_SERVER_NAME', '')
FILENAME_TEMPLATE = getattr(settings, 'DBBACKUP_FILENAME_TEMPLATE', '{databasename}-{servername}-{datetime}.{extension}')


##################################
#  MySQL Settings
##################################

class MYSQL_SETTINGS:
    EXTENSION = getattr(settings, 'DBBACKUP_MYSQL_EXTENSION', 'mysql')
    BACKUP_COMMANDS = getattr(settings, 'DBBACKUP_MYSQL_BACKUP_COMMANDS', [
        shlex.split('mysqldump -u{username} -p{password} {databasename} >'),
    ])
    RESTORE_COMMANDS = getattr(settings, 'DBBACKUP_MYSQL_RESTORE_COMMANDS', [
        shlex.split('mysql -u{username} -p{password} {databasename} <'),
    ])


##################################
#  PostgreSQL Settings
##################################

class POSTGRESQL_SETTINGS:
    EXTENSION = getattr(settings, 'DBBACKUP_POSTGRESQL_EXTENSION', 'psql')
    BACKUP_COMMANDS = getattr(settings, 'DBBACKUP_POSTGRESQL_BACKUP_COMMANDS', [
        shlex.split('pg_dump -p {port} -U {username} {databasename} >'),
    ])
    RESTORE_COMMANDS = getattr(settings, 'DBBACKUP_POSTGRESQL_RESTORE_COMMANDS', [
        shlex.split('dropdb -p {port} -U {username} {databasename}'),
        shlex.split('createdb -p {port} -U {username} {databasename} --owner={username}'),
        shlex.split('psql -p {port} -U {username} -1 {databasename} <'),
    ])


##################################
#  Sqlite Settings
##################################

class SQLITE_SETTINGS:
    EXTENSION = getattr(settings, 'DBBACKUP_SQLITE_EXTENSION', 'sqlite')
    BACKUP_COMMANDS = getattr(settings, 'DBBACKUP_SQLITE_BACKUP_COMMANDS', [
        [READ_FILE, '{databasename}'],
    ])
    RESTORE_COMMANDS = getattr(settings, 'DBBACKUP_SQLITE_RESTORE_COMMANDS', [
        [WRITE_FILE, '{databasename}'],
    ])


##################################
#  DBCommands Class
##################################

class DBCommands:
    """ Process the Backup or Restore commands. """

    def __init__(self, database):
        self.database = database
        self.engine = self.database['ENGINE'].split('.')[-1]
        self.settings = self._get_settings()

    def _get_settings(self):
        """ Returns the proper settings dictionary. """
        if self.engine == 'mysql': return MYSQL_SETTINGS
        elif self.engine in ('postgresql_psycopg2', 'postgis',): return POSTGRESQL_SETTINGS
        elif self.engine == 'sqlite3': return SQLITE_SETTINGS

    def filename(self, servername=None, wildcard=None):
        """ Create a new backup filename. """
        datestr = wildcard or datetime.now().strftime(DATE_FORMAT)
        filename = FILENAME_TEMPLATE.replace('{databasename}', self.database['NAME'])
        filename = filename.replace('{servername}', servername or SERVER_NAME)
        filename = filename.replace('{datetime}', datestr)
        filename = filename.replace('{extension}', self.settings.EXTENSION)
        filename = filename.replace('--', '-')
        return filename

    def filename_match(self, servername=None, wildcard='*'):
        """ Return the prefix for backup filenames. """
        return self.filename(servername, wildcard)

    def filter_filepaths(self, filepaths, servername=None):
        """ Returns a list of backups file paths from the dropbox entries. """
        regex = self.filename_match(servername, '.*?')
        return filter(lambda path: re.search(regex, path), filepaths)

    def translate_command(self, command):
        """ Translate the specified command. """
        command = copy.copy(command)
        for i in range(len(command)):
            command[i] = command[i].replace('{username}', self.database.get('ADMINUSER', self.database['USER']))
            command[i] = command[i].replace('{password}', self.database['PASSWORD'])
            command[i] = command[i].replace('{databasename}', self.database['NAME'])
            command[i] = command[i].replace('{port}', str(self.database['PORT']))
        return command

    def run_backup_commands(self, stdout):
        """ Translate and run the backup commands. """
        return self.run_commands(self.settings.BACKUP_COMMANDS, stdout=stdout)

    def run_restore_commands(self, stdin):
        """ Translate and run the backup commands. """
        stdin.seek(0)
        return self.run_commands(self.settings.RESTORE_COMMANDS, stdin=stdin)

    def run_commands(self, commands, stdin=None, stdout=None):
        """ Translate and run the specified commands. """
        for command in commands:
            command = self.translate_command(command)
            if (command[0] == READ_FILE): self.read_file(command[1], stdout)
            elif (command[0] == WRITE_FILE): self.write_file(command[1], stdin)
            else: self.run_command(command, stdin, stdout)

    def run_command(self, command, stdin=None, stdout=None):
        """ Run the specified command. """
        devnull = open(os.devnull, 'w')
        pstdin = stdin if command[-1] == '<' else None
        pstdout = stdout if command[-1] == '>' else devnull
        command = filter(lambda arg: arg not in ['<', '>'], command)
        print "  Running: %s" % ' '.join(command)
        process = Popen(command, stdin=pstdin, stdout=pstdout)
        process.wait()
        devnull.close()
        if process.poll():
            raise CommandError("Error running: %s" % command)

    def read_file(self, filepath, stdout):
        """ Read the specified file to stdout. """
        print "  Reading: %s" % filepath
        stdout.write(open(filepath, 'r').read())

    def write_file(self, filepath, stdin):
        """ Write the specified file from stdin. """
        print "  Writing: %s" % filepath
        writehandle = open(filepath, 'w')
        writehandle.write(stdin.read())
        writehandle.close()
