=====================
Django Dropbox Backup
=====================

This is a Django app that provides management commands to help backup and
restore your project database to Dropbox.

WARNING: Running 'dbrestore' will delete your current datatabase.  Do not
attempt to run this command if you are not sure that you already have a
valid backup file.


OVERVIEW
--------
After setting up the required configuration options and calling the 'dbbackup'
or 'dbrestore' admin commands for the first time, you will be  be prompted
with a verification URL to allow this script to access your Dropbox files.
After verification, a small user token will be stored in the database for
future use when this script is called.

When 'dbbackup' is called, a backup of your database will be created and
stored remotely into the Dropbox directory specified by
DROPBOX_BACKUP_REMOTE_DIR.

When 'dbrestore' is called, the latest backup (by default) will be read from
the Dropbox directory specified by DROPBOX_BACKUP_REMOTE_DIR.  The script will
then perform DROPDB and CREATEDB commands specific to your database and then
load the backed up information into the currently empty database.

The filename generated on the remote machine will be the format specified by
DROPBOX_BACKUP_FILENAME which is '{databasename}-{servername}-{datetime}.db'
by default.  The {servername} option is user specified either in settings.py
or on the command line when calling the 'dbbackup' or 'dbrestore' scripts.


REQUIRED SETTINGS
-----------------
DROPBOX_CONSUMER_KEY    - The Consumer Key provided to you by Dropbox.
DROPBOX_CONSUMER_SECRET - The Consumer Secret provided to you by Dropbox.
DBBACKUP_TOKEN_FILEPATH - The local filepath to store Dropbox oAuth request
                          and access tokens.


OPTIONAL DBBACKUP SETTINGS
--------------------------
DBBACKUP_REMOTE_DIR  - Remote dropbox directory to save created db backup
                       files. Default: '/django-dbbackups/'
DBBACKUP_SERVER_NAME - Server name to append to the created db filenames.
                       Leave this blank to not include a servername attribute
                       on the generated backup filenames. Default: ''
DBBACKUP_DATE_FORMAT - Date format to use when appending the datetime to the
                       generated backup filenames. Default: '%Y-%m-%d-%H%M%S'
DBBACKUP_FILENAME    - Template to use when generating new backup filenames.
                       Valid template tags include {databasename},
                       {servername}, {datetime}.
                       Default: '{databasename}-{servername}-{datetime}.db'
DBBACKUP_DATABASES   - Database keys to backup from settings.py
                       Default: [db['NAME'] for db in settings.DATABASES]


OPTIONAL DROPBOX SETTINGS
-------------------------
These settings are ported over from the Dropbox API.  You can read more about
them from the Dropbox API website. If you do not know what these options are
for then you will probably be fine just leaving them alone.

DROPBOX_VERIFIER          - May be a required setting in the future.
                            Default: ''
DROPBOX_SERVER            - Default: 'api.dropbox.com'
DROPBOX_CONTENT_SERVER    - Default: 'api-content.dropbox.com'
DROPBOX_PORT              - Default: 80
DROPBOX_REQUEST_TOKEN_URL - Default: 'https://api.dropbox.com/0/oauth/request_token'
DROPBOX_ACCESS_TOKEN_URL  - Default: 'https://api.dropbox.com/0/oauth/access_token'
DROPBOX_AUTHORIZATION_URL - Default: 'https://www.dropbox.com/0/oauth/authorize'
DROPBOX_ROOT              - Default: 'dropbox'


DJANGO ADMIN COMMANDS
---------------------
dbbackup [--servername=<name>] [--database=<dbkey>] [--clean]

  Backup the database(s) to Dropbox.  If 'servername' is specified, it will be
  included in the generated backup filename.  If 'database' is specified, only
  the django database with the specified key will be backed up.  If 'clean' is
  set, all but the last 10 backups and any backups that occured on the first of
  the month will be deleted from Dropbox.


dbrestore [--database=<dbkey>] [--filename] [--servername=<name>] 

  Restore a single database from a backup stored on Dropbox.  If you have more
  than 1 database defined in your settings.py file, then the 'database' name
  is required (otherwise it's optional).  If 'filename' is specified, that
  file will be used to restore the database.  If 'servername' is specified it
  will override the DBBACKUP_SERVER_NAME defined in settings.py and the latest
  database backup matching dbname and servername will be used to restore.
