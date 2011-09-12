=======================
 Django Dropbox Backup
=======================

This Django application provides management commands to help backup and
restore your project database to AmazonS3, Dropbox or Local Disk.

* Keep your important data secure and offsite.
* Use Crontab or Celery to setup automated backups.
* Great to keep your development database up to date.

WARNING: Running 'dbrestore' will delete your current datatabase.  Do not
attempt to run this command if you are not sure that you already have a
valid backup file.


MANAGEMENT COMMANDS
-------------------
DBBackup  - Backup your database to the specified storage. By default this
            will backup all databases specified in your settings.py file and
            will not delete any old backups. You can optionally specify a
            server name to be included in the backup filename.
            >> dbbackup [-s <servername>] [-d <database>] [--clean]

DBRestore - Restore your database from the specified storage. By default this
            will lookup the latest backup and restore from that. You may
            optionally specify a servername if you you want to backup a
            database image that was created from a different server. You may
            also specify an explicit local file to backup from.
            >> dbrestore [-d <database>] [-s <servername>] [-f <localfile>]



=======================
 DBBackup to Amazon S3
=======================

In order to backup to Amazon S3, you'll first need to create an Amazon
Webservices Account and setup your Amazon S3 bucket. Once that is complete,
you can follow the required setup below.


SETUP YOUR DJANGO PROJECT
-------------------------
1. Install django-dbbackup and the required simples3 dependancy:
   >> cd django-dbbackup
   >> python setup.py install
   >> pip install simples3

2. Add 'dbbackup' to INSTALLED_APPS in your settings.py file.

3. Include the required settings below.
   DBBACKUP_STORAGE = 'dbbackup.storage.s3_storage'
   DBBACKUP_S3_BUCKET = '<amazon_bucket_name>'
   DBBACKUP_S3_ACCESS_KEY = '<amazon_access_key>'
   DBBACKUP_S3_SECRET_KEY = '<amazon_secret_key>'

4. Now you're ready to use the backup management commands.


AVAILABLE SETTINGS
------------------
DBBACKUP_S3_BUCKET (required)
    The name of the Amazon S3 bucket to store your backups. This directory
    must exist before attempting to create your first backup.

DBBACKUP_S3_ACCESS_KEY (required)
    Your Amazon Account Access Key. This can be found on your Amazon Account
    Security Credentials page. Note: Do not share this key with anyone you do
    not trust with access to your Amazon files.

DBBACKUP_S3_SECRET_KEY (required)
    Your Amazon Account Secret Key. This can be found in the same location as
    your Access Key above.

DBBACKUP_S3_DIRECTORY (optional)
    The directory in your Amazon S3 bucket you wish to save your backups. By
    default this is set to 'django-dbbackups/'.

DBBACKUP_S3_DOMAIN (optional)
    Optionally specify the Amazon domain to use when transferring the
    generated backup files.



=====================
 DBBackup to Dropbox
=====================

In order to backup to Dropbox, you'll first need to create a Dropbox Account
and set it up to communicate with the Django-DBBackup application. Don't
worry, all instructions are below.


SETUP YOUR DROPBOX ACCOUNT
--------------------------
1. Login to Dropbox and navigate to Developers » MyApps.

2. Click the button to create a new app and name it whatever you like. For
   reference, I named mine 'Website Backups'.

3. After your app is created, note the options button and more importantly
   the 'App Key' and 'App Secret' values inside. You'll need those later.


SETUP YOUR DJANGO PROJECT
-------------------------
1. Install django-dbbackup and the required Python Dropbox Client API. If
   using Pip, you can install this package using the following command:
   >> cd django-dbbackup
   >> python setup.py install
   >> pip install hg+https://bitbucket.org/dropboxapi/dropbox-client-python

2. Add 'dbbackup' to INSTALLED_APPS in your settings.py file.

3. Include the required settings below.
   DBBACKUP_STORAGE = 'dbbackup.storage.dropbox_storage'
   DBBACKUP_TOKENS_FILEPATH = '<local_tokens_filepath>'
   DBBACKUP_DROPBOX_CONFIG = {  # Dropbox API Configuration
       'consumer_key': '<dropbox_app_key>',
       'consumer_secret': '<dropbox_app_secret>',
   }

4. Now you're ready to use the backup management commands. The first time you
   run a command you'll be prompted to visit a Dropbox URL to allow DBBackup
   access to your Dropbox account.


AVAILABLE SETTINGS
------------------
DBBACKUP_TOKENS_FILEPATH (required)
    The local filepath to store the Dropbox oAuth request and tokens. This file
    will be auto-created, but should be treated like any other password to
    access your website. NOTE: Do not share these keys with anyone you do not
    trust with access to your Dropbox files.

DBBACKUP_DROPBOX_CONFIG (required)
    Dictionary containing Dropbox API configuration settings. Most of the
    settings contain defaults that you do not need to worry about. However, the
    two settings 'consumer_key' & 'consumer_secret' are required. You should
    refer to the Dropbox API documention to see a list of other settings
    available.

DBBACKUP_DROPBOX_DIRECTORY (optional)
    The directory in Dropbox you wish to save your backups. By default this is
    set to '/django-dbbackups/'.


========================
 DBBackup to Local Disk
========================

To store your database backups on the local filesystem, simply setup the
required settings below. Storing backups to local disk may also be useful for
Dropbox if you already have the offical Dropbox client installed on your
system.


SETUP YOUR DJANGO PROJECT
-------------------------
1. Install django-dbbackup application:
   >> cd django-dbbackup
   >> python setup.py install

2. Add 'dbbackup' to INSTALLED_APPS in your settings.py file.

3. Include the required settings below.
   DBBACKUP_STORAGE = 'dbbackup.storage.filesystem'
   DBBACKUP_FILESYSTEM_DIRECTORY = '<local_directory_path>'

4. Now you're ready to use the backup management commands.


AVAILABLE SETTINGS
------------------
DBBACKUP_FILESYSTEM_DIRECTORY (required)
    The directory on your local system you wish to save your backups.



===================
 DATABASE SETTINGS
===================

The following databases are supported by this application. You can customize
the commands used for backup and the resulting filenames with the following
settings.


MYSQL
-----
DBBACKUP_MYSQL_EXTENSION (optional)
    Entension to use for a mysql backup. By default this is 'mysql'.

DBBACKUP_MYSQL_BACKUP_COMMANDS (optional)
    List of commands to use execute when creating a backup. Commands are sent
    to popen and should be split into shlex tokens. By default, the following
    command is run:
    >> mysqldump -u{username} -p{password} {databasename} >

DBBACKUP_MYSQL_RESTORE_COMMANDS (optional)
    List of commands to use execute when creating a backup. Commands are sent
    to popen and should be split into shlex tokens. By default, the following
    command is run:
    >> mysql -u{username} -p{password} {databasename} <


POSTGRES
--------
DBBACKUP_POSTGRES_EXTENSION (optional)
    Entension to use for a postgres backup. By default this is 'psql'.

DBBACKUP_POSTGRES_BACKUP_COMMANDS (optional)
    List of commands to use execute when creating a backup. Commands are sent
    to popen and should be split into shlex tokens. By default, the following
    command is run:
    >> pg_dump {databasename} >

DBBACKUP_POSTGRES_RESTORE_COMMANDS (optional)
    List of commands to use execute when restoring a backup. Commands are sent
    to popen and should be split into shlex tokens. By default, the following
    commands are run:
    >> dropdb {databasename}
    >> createdb {databasename} --owner={username}
    >> psql -1 {databasename} <


SQLITE
------
DBBACKUP_SQLITE_EXTENSION (optional)
    Entension to use for an sqlite backup. By default this is 'sqlite'.

DBBACKUP_SQLITE_BACKUP_COMMANDS (optional)
    List of commands to use execute when creating a backup. Commands are sent to
    popen and should be split into shlex tokens. By default, the following
    command is run:
    >> [READ_FILE, '{databasename}']

DBBACKUP_SQLITE_RESTORE_COMMANDS (optional)
    List of commands to use execute when restoring a backup. Commands are sent
    to popen and should be split into shlex tokens. By default, the following
    command is run:
    >> [WRITE_FILE, '{databasename}']



==========================
 DEFINING BACKUP COMMANDS
==========================

When creating backup or restore commands, there are a few template variables
you can use in the commands (listed below). Also note, ending a command with >
or < will pipe the file contents from or to the command respectively.

    {databasename}: Name of the database from settings.py
    {servername}: Optional SERVER_NAME setting in settings.py
    {datetime}: Current datetime string (see DBBACKUP_DATE_FORMAT).
    {extension}: File extension for the current database.

There are also two special commands READ_FILE and WRITE_FILE which take the
form of a two-item list, the second item being the file to read or write.
Please see the SQLite settings above for reference.



=================
 GLOBAL SETTINGS
=================
DBBACKUP_STORAGE (required)
    String pointing to django-dbbackup location module to use when performing a
    backup. You can see the exact definitions to use in the required settings
    for the backup location of your choice above.

DBBACKUP_DATE_FORMAT (optional)
    The Python datetime format to use when generating the backup filename. By
    default this is '%Y-%m-%d-%H%M%S'.

DBBACKUP_SERVER_NAME (optional)
    An optional server name to use when generating the backup filename. This is
    useful to help distinguish between development and production servers. By
    default this value is not used and the servername is not included in the
    generated filename.

DBBACKUP_FILENAME_TEMPLATE (optional)
    The template to use when generating the backup filename. By default this is
    '{databasename}-{servername}-{datetime}.{extension}'.
