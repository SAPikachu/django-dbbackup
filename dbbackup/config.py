"""
Loads Dropbox Configuration
  
Required Settings:
  DROPBOX_CONSUMER_KEY          - Consumer Key from Dropbox.com
  DROPBOX_CONSUMER_SECRET       - Consumer Secret from Dropbox.com
  DROPBOX_VERIFIER              - Leave blank string (for now)
  DROPBOX_BACKUP_AUTH_USERNAME  - Django username to save backup oAuth keys as.
"""

from django.conf import settings

CONFIG = {
    # Required Settings
    'consumer_key': settings.DROPBOX_CONSUMER_KEY,
    'consumer_secret': settings.DROPBOX_CONSUMER_SECRET,
    'backup_auth_username': settings.DBBACKUP_AUTH_USERNAME,
    
    # Optional Backup & Restore Options
    'backup_localwork_dir': getattr(settings, 'DBBACKUP_LOCALWORK_DIR', "/tmp/"),
    'backup_remote_dir': getattr(settings, 'DBBACKUP_REMOTE_DIR', "/django-dbbackups/"),
    'backup_server_name': getattr(settings, 'DBBACKUP_SERVER_NAME', ""),
    'backup_date_format': getattr(settings, 'DBBACKUP_DATE_FORMAT', "%Y-%m-%d-%H%M%S"),
    'backup_filename': getattr(settings, 'DBBACKUP_FILENAME', "{databasename}-{servername}-{datetime}.db"),
    'backup_databases': getattr(settings, 'DBBACKUP_DATABASES', settings.DATABASES.keys()),
    
    # Backup Commands
    'backup': getattr(settings, 'DBBACKUP_COMMANDS', {
        'mysql': [["mysqldump -u {username} -p {password} {databasename} > {backupfile}"]],
        'postgresql': [["pg_dump", "{databasename}", "--format=tar", "--file={backupfile}"]],
        'postgresql_psycopg2': [["pg_dump", "{databasename}", "--format=tar", "--file={backupfile}"]],
        'sqlite3': [["cp", "{databasename}", "{backupfile}"]],
    }),
    
    # Restore Commands
    'restore': getattr(settings, 'DBRESTORE_COMMANDS', {
        'mysql': [["mysql -u {username} -p{password} {databasename} < {backupfile}"]],
        'postgresql': [["dropdb", "{databasename}"], ["createdb", "{databasename}", "--owner={username}"], ["pg_restore", "--dbname={databasename}", "{backupfile}"]],
        'postgresql_psycopg2': [["dropdb", "{databasename}"], ["createdb", "{databasename}", "--owner={username}"], ["pg_restore", "--dbname={databasename}", "{backupfile}"]],
        'sqlite3': [["cp", "{backupfile}", "{databasename}"]],
    }),
    
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
