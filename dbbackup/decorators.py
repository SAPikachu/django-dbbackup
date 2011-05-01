"""
DBBackup decorators
"""
import sys
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection
from django.http import HttpRequest
from django.views.debug import ExceptionReporter
from functools import wraps

FAKE_REQUEST = HttpRequest()
FAKE_REQUEST.META['SERVER_NAME'] = ''
FAKE_REQUEST.META['SERVER_PORT'] = ''


def email_uncaught_exception(func):
    """ Creates a lock file to make sure two instances of this cronjob will
        not be running at the same time. If the lock is obtained successfully,
        it will run the function and email any uncaught exception to ADMINS.
    """
    module = func.__module__
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            excType, excValue, traceback = sys.exc_info()
            reporter = ExceptionReporter(FAKE_REQUEST, excType, excValue, traceback.tb_next)
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
