""" .

Configuration
=============

You should add ``adrest`` to your ``INSTALLED_APPS`` in Django settings.

Also you can redefine default **ADRest** settings writen bellow.


"""
try:
    from django.core.exceptions import ImproperlyConfigured
    from django.conf import settings

    getattr(settings, 'DEBUG')

except (ImportError, ImproperlyConfigured):

    settings.configure()

from .utils.tools import as_tuple


#: Enable ADRest API logs. Information about requests and responses will be
#: saved in database.
ADREST_ACCESS_LOG = getattr(settings, 'ADREST_ACCESS_LOG', False)

#: Create `adrest.models.AccessKey` models for authorisation by keys
ADREST_ACCESSKEY = getattr(
    settings, 'ADREST_ACCESSKEY',
    'django.contrib.auth' in getattr(settings, 'INSTALLED_APPS', tuple()))

#: Create AccessKey for Users automaticly
ADREST_AUTO_CREATE_ACCESSKEY = getattr(
    settings, 'ADREST_AUTO_CREATE_ACCESSKEY', False)

#: Set default number resources per page for pagination
#: ADREST_LIMIT_PER_PAGE = 0 -- Disabled pagination by default
ADREST_LIMIT_PER_PAGE = int(getattr(settings, 'ADREST_LIMIT_PER_PAGE', 50))

#: Dont parse a exceptions. Show standart Django 500 page.
ADREST_DEBUG = getattr(settings, 'ADREST_DEBUG', False)

#: List of errors for ADRest's errors mails.
#: Set ADREST_MAIL_ERRORS = None for disable this functionality
ADREST_MAIL_ERRORS = as_tuple(getattr(settings, 'ADREST_MAIL_ERRORS', 500))

#: Set maximum requests per timeframe
ADREST_THROTTLE_AT = getattr(settings, 'ADREST_THROTTLE_AT', 120)

#: Set timeframe length
ADREST_THROTTLE_TIMEFRAME = getattr(settings, 'ADREST_THROTTLE_TIMEFRAME', 60)

#: We do not restrict access for OPTIONS request.
ADREST_ALLOW_OPTIONS = getattr(settings, 'ADREST_ALLOW_OPTIONS', False)

#: Template path for ADRest map
ADREST_MAP_TEMPLATE = getattr(settings, 'ADREST_MAP_TEMPLATE', 'api/map.html')
