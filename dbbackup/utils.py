"""
Util functions for dropbox application.
"""
import re
import datetime
import os
import subprocess
from .config import CONFIG


def backup_filename(database):
    """ Create a new backup filename. """
    dateTimeStr = datetime.datetime.now().strftime(CONFIG['backup_date_format'])
    fileName = CONFIG['backup_filename']
    fileName = fileName.replace('{databasename}', database['NAME'])
    fileName = fileName.replace('{servername}', CONFIG['backup_server_name'])
    fileName = fileName.replace('{datetime}', dateTimeStr)
    fileName = fileName.replace('--', '-')
    return fileName


def backup_filename_match(database, wildcard='*'):
    """ Return the prefix for backup filenames. """
    fileMatch = CONFIG['backup_filename']
    fileMatch = fileMatch.replace('{databasename}', database['NAME'])
    fileMatch = fileMatch.replace('{servername}', CONFIG['backup_server_name'])
    fileMatch = fileMatch.replace('{datetime}', wildcard)
    fileMatch = fileMatch.replace('--', '-')
    return fileMatch


def filter_backups(entries, database):
    """ Returns a list of backups file paths from the dropbox entries. """
    backups = []
    for entry in entries:
        if (not entry['is_dir']):
            fileMatch = backup_filename_match(database, '.*?')
            if (re.search(fileMatch, entry['path'])):
                backups.append(entry['path'])
    return backups


def get_commands(database, backupfile, cmdname):
    """ Create the backup command. """
    databaseEngine = database['ENGINE'].split('.')[-1]
    commands = CONFIG[cmdname][databaseEngine]
    for i in range(len(commands)):
        for j in range(len(commands[i])):
            commands[i][j] = commands[i][j].replace('{username}', database['USER'])
            commands[i][j] = commands[i][j].replace('{password}', database['PASSWORD'])
            commands[i][j] = commands[i][j].replace('{databasename}', database['NAME'])
            commands[i][j] = commands[i][j].replace('{backupfile}', backupfile)
    return commands


def run_command(cmd, rstdout=False, **kwargs):
    """ Execute a local command. If rstdout is True then the stdout string
        will be returned. Otherwise the return code will be returned.
    """
    if (rstdout):
        # Return Standard Out
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, **kwargs)
        stdout = process.communicate()[0]
        retcode = process.poll()
        if (retcode):
            raise Exception("Command Error: %s\n%s" % (cmd, stdout))
        return stdout
    else:
        # Pipe Stdout to the command line (Return retcode)
        process = subprocess.Popen(cmd, **kwargs)
        process.wait()
        retcode = process.poll()
        if (retcode): raise Exception("Command Error: %s" % cmd)
        return retcode