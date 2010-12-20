"""
Util functions for dropbox application.
"""
import copy
import re
import sys
from .config import COMMAND_READ
from .config import COMMAND_WRITE
from .config import CONFIG
from .config import DBMAP
from .models import DropboxTokenFile
from .models import DropboxNotAuthorized
from datetime import datetime
from os import path
from subprocess import Popen

BYTES = (
    ('PB', 1125899906842624.0),
    ('TB', 1099511627776.0),
    ('GB', 1073741824.0),
    ('MB', 1048576.0),
    ('KB', 1024.0),
    ('B', 1.0),
)


###################################
#  Generally Useful Functions
###################################

def bytesToStr(byteVal, decimals=1):
    """ Convert bytes to a human readable string. """
    for unit, byte in BYTES:
        if (byteVal >= byte):
            if (decimals == 0):
                return "%s %s" % (int(round(byteVal / byte, 0)), unit)
            else:
                return "%s %s" % (round(byteVal / byte, decimals), unit)
    return "%s B" % byteVal


###################################
#  Backup & Restore Utilities
###################################

def backup_filename(database, wildcard=None):
    """ Create a new backup filename. """
    dbName = path.basename(database['NAME'].split('.')[0])
    dateStr = wildcard if wildcard else datetime.now().strftime(CONFIG['backup_date_format'])
    fileName = CONFIG['backup_filename']
    fileName = fileName.replace('{databasename}', dbName)
    fileName = fileName.replace('{servername}', CONFIG['backup_server_name'])
    fileName = fileName.replace('{datetime}', dateStr)
    fileName = fileName.replace('{extension}', DBMAP[dbengine(database)]['ext'])
    fileName = fileName.replace('--', '-')
    return fileName


def backup_filename_match(database, wildcard='*'):
    """ Return the prefix for backup filenames. """
    return backup_filename(database, wildcard)


def dbengine(database):
    """ Return the simple database engine name for the specified database. """
    return database['ENGINE'].split('.')[-1]


def filter_backups(entries, database):
    """ Returns a list of backups file paths from the dropbox entries. """
    backups = []
    for entry in entries:
        if (not entry['is_dir']):
            fileMatch = backup_filename_match(database, '.*?')
            if (re.search(fileMatch, entry['path'])):
                backups.append(entry['path'])
    return backups


def get_dropbox_client():
    """ Same as models.UserToken.get_dropbox_client() but with useful
        print messages for the command line and quits on error.
    """
    try:
        print "Connecting to Dropbox"
        dbtokens = DropboxTokenFile(CONFIG['token_filepath'])
        return dbtokens.get_dropbox_client()
    except DropboxNotAuthorized, e:
        print "Account not Authorized."
        print "Please visit the following URL to active your account:"
        print e.url
        sys.exit(1)


def run_backup_commands(database, stdout=None):
    """ Translate and run the backup commands for the specified database. """
    engine = DBMAP[dbengine(database)]['db']
    commands = CONFIG['commands'][engine]['backup']
    return run_commands(commands, database, stdout=stdout)


def run_restore_commands(database, stdin=None):
    """ Translate and run the restore commands for the specified database. """
    engine = DBMAP[dbengine(database)]['db']
    commands = CONFIG['commands'][engine]['restore']
    return run_commands(commands, database, stdin=stdin)


def run_commands(commands, database, stdin=None, stdout=None):
    """ Translate and run the commands for the specified database. """
    for command in commands:
        command = copy.deepcopy(command)
        # Translate command arguments
        for i in range(len(command)):
            command[i] = command[i].replace('{username}', database['USER'])
            command[i] = command[i].replace('{password}', database['PASSWORD'])
            command[i] = command[i].replace('{databasename}', database['NAME'])
        # Run the specified command
        if (command[0] == COMMAND_READ):
            # Read command[1] filepath to stdout
            print "  Reading: %s" % command[1]
            stdout.write(open(command[1], 'r').read())
        elif (command[0] == COMMAND_WRITE):
            # Write command[1] filepath to stdin
            print "  Writing: %s" % command[1]
            writehandle = open(command[1], 'w')
            writehandle.write(stdin.read())
            writehandle.close()
        else:
            # Use subprocess.Popen to run the command
            pstdin = stdin if command[-1] == '<' else None
            pstdout = stdout if command[-1] == '>' else None
            command = filter(lambda arg: arg not in ['<', '>'], command)
            print "  Running: %s" % ' '.join(command)
            process = Popen(command, stdin=pstdin, stdout=pstdout)
            process.wait()
            if (process.poll()):
                sys.exit("Error running: %s" % command)
