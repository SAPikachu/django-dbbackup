"""
Util functions for dropbox application.
"""
import sys
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection
from django.http import HttpRequest
from django.views.debug import ExceptionReporter
from functools import wraps

FAKE_HTTP_REQUEST = HttpRequest()
FAKE_HTTP_REQUEST.META['SERVER_NAME'] = ''
FAKE_HTTP_REQUEST.META['SERVER_PORT'] = ''

BYTES = (('PB', 1125899906842624.0), ('TB', 1099511627776.0), ('GB', 1073741824.0),
    ('MB', 1048576.0), ('KB', 1024.0), ('B', 1.0))


###################################
#  Display Filesizes
###################################

def bytes_to_str(byteVal, decimals=1):
    """ Convert bytes to a human readable string. """
    for unit, byte in BYTES:
        if (byteVal >= byte):
            if (decimals == 0):
                return "%s %s" % (int(round(byteVal / byte, 0)), unit)
            else:
                return "%s %s" % (round(byteVal / byte, decimals), unit)
    return "%s B" % byteVal

def handle_size(filehandle):
    """ Given a filehandle return the filesize. """
    filehandle.seek(0, 2)
    return bytes_to_str(filehandle.tell())


###################################
#  Email Exception Decorator
###################################

def email_uncaught_exception(func):
    """ Email uncaught exceptions to the SERVER_EMAIL. """
    module = func.__module__
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            if getattr(settings, 'DBBACKUP_SEND_EMAIL', True):
                excType, excValue, traceback = sys.exc_info()
                reporter = ExceptionReporter(FAKE_HTTP_REQUEST, excType, excValue, traceback.tb_next)
                subject = "Cron: Uncaught exception running %s" % module
                body = reporter.get_traceback_html()
                msgFrom = settings.SERVER_EMAIL
                msgTo = [admin[1] for admin in settings.ADMINS]
                message = EmailMessage(subject, body, msgFrom, msgTo)
                message.content_subtype = 'html'
                message.send(fail_silently=True)
            raise
        finally:
            connection.close()
    return wrapper
