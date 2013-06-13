""" ADRest mail utils. """
import traceback
import sys
from django.core.mail import mail_admins
from ..settings import ADREST_MAIL_ERRORS


def adrest_errors_mail(response, request):
    """ Send a mail about ADRest errors.

    :return bool: status of operation

    """

    if not response.status_code in ADREST_MAIL_ERRORS:
        return False

    subject = 'ADREST API Error (%s): %s' % (
        response.status_code, request.path)
    stack_trace = '\n'.join(traceback.format_exception(*sys.exc_info()))
    message = """
Stacktrace:
===========
%s

Handler data:
=============
%s

Request information:
====================
%s

""" % (stack_trace, repr(getattr(request, 'data', None)), repr(request))
    return mail_admins(subject, message, fail_silently=True)
