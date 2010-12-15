"""
Loads Dropbox Configuration
  
Required Settings:
  DROPBOX_CONSUMER_KEY          - Consumer Key from Dropbox.com
  DROPBOX_CONSUMER_SECRET       - Consumer Secret from Dropbox.com
  DROPBOX_VERIFIER              - Leave blank string (for now)
  DROPBOX_BACKUP_AUTH_USERNAME  - Django username to save backup oAuth keys as.
"""

from django.conf import settings

COMMAND_READ = "<read>:"
COMMAND_WRITE = "<write>:"
DBMAP = {
    'mysql': 'mysql',
    'postgresql': 'postgresql',
    'postgresql_psycopg2': 'postgresql',
    'sqlite3': 'sqlite3',
}

CONFIG = {
    # Required Settings
    'consumer_key': settings.DROPBOX_CONSUMER_KEY,
    'consumer_secret': settings.DROPBOX_CONSUMER_SECRET,
    'token_filepath': settings.DBBACKUP_TOKEN_FILEPATH,
    
    # Optional Backup & Restore Options
    'backup_remote_dir': getattr(settings, 'DBBACKUP_REMOTE_DIR', "/django-dbbackups/"),
    'backup_server_name': getattr(settings, 'DBBACKUP_SERVER_NAME', ""),
    'backup_date_format': getattr(settings, 'DBBACKUP_DATE_FORMAT', "%Y-%m-%d-%H%M%S"),
    'backup_filename': getattr(settings, 'DBBACKUP_FILENAME', "{databasename}-{servername}-{datetime}.db"),
    'backup_databases': getattr(settings, 'DBBACKUP_DATABASES', settings.DATABASES.keys()),
    
    # Backup & Restore Commands
    # Note: Use < & > in the command definition to denote that stdin 
    # or stdout arguments are required input or output pipes respectivly.
    'commands': {
        'mysql': getattr(settings, 'DBBACKUP_MYSQL_COMMANDS', {
            'backup': [['mysqldump', '-u{username}', '-p{password}', '{databasename}', '>']],
            'restore': [['mysql', '-u{username}', '-p{password}', '{databasename}', '<']],
        }),
        'postgresql': getattr(settings, 'DBBACKUP_POSTGRESQL_COMMANDS', {
            'backup': [['pg_dump', '{databasename}', '>']],
            'restore': [['dropdb', '{databasename}'], ['createdb', '{databasename}', '--owner={username}'], ['psql', '{databasename}', '<']],
        }),
        'sqlite3': getattr(settings, 'DBBACKUP_POSTGRESQL_COMMANDS', {
            'backup': [[COMMAND_READ, '{databasename}']],
            'restore': [[COMMAND_WRITE, '{databasename}']],
        }),
    },
    
    # Optional Dropbox Settings
    # Don't change these unless you know what you're doing.
    'verifier': getattr(settings, 'DROPBOX_VERIFIER', ''),
    'server': getattr(settings, 'DROPBOX_SERVER', 'api.dropbox.com'),
    'content_server': getattr(settings, 'DROPBOX_CONTENT_SERVER', 'api-content.dropbox.com'),
    'port': getattr(settings, 'DROPBOX_PORT', 80),
    'request_token_url': getattr(settings, 'DROPBOX_REQUEST_TOKEN_URL', 'https://api.dropbox.com/0/oauth/request_token'),
    'access_token_url': getattr(settings, 'DROPBOX_ACCESS_TOKEN_URL', 'https://api.dropbox.com/0/oauth/access_token'),
    'authorization_url': getattr(settings, 'DROPBOX_AUTHORIZATION_URL', 'https://www.dropbox.com/0/oauth/authorize'),
    'root': getattr(settings, 'DROPBOX_ROOT', 'dropbox'),
}
