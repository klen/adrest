#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Adrest errors notifiers
"""
from logging import getLogger
import traceback
import sys
from django.core.mail import mail_admins
from ..settings import ADREST_CONFIG

api_logger = getLogger(ADREST_CONFIG['LOGGER_NAME'])


def email_notifier(request, response):
    """ Send a mail about ADRest errors.

    :return bool: status of operation

    """

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


def logging_notifier(request, response):
    """Notify logging about errors\

    :param request: :class:``django.http.Request``
    :param response: :class:``django.http.HttpResponse``
    """

    api_logger.error("ADREST API Error {0}: {1}".format(response.status_code, request.path),
                     exc_info=True,
                     extra={"data": {
                         "request_data": repr(getattr(request, 'data', None)),
                         "response_data": response.content,
                         "request": repr(request)},
                            'stack': True})
