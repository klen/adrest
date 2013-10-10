"""
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

from adrest.utils.tools import get_notifiers


ADREST_CONFIG = {
    #: Enable ADRest API logs. Information about requests and responses will be
    #: saved in database.
    "ACCESS_LOG": False,

    #: Create `adrest.models.AccessKey` models for authorisation by keys
    "ACCESSKEY": 'django.contrib.auth' in getattr(settings, 'INSTALLED_APPS', tuple()),

    #: Create AccessKey for Users automaticly
    "AUTO_CREATE_ACCESSKEY": False,

    #: Set default number resources per page for pagination
    #: LIMIT_PER_PAGE = 0 -- Disabled pagination by default
    "LIMIT_PER_PAGE": 50,

    #: Dont parse a exceptions. Show standart Django 500 page.
    "DEBUG": False,

    #: List of errors for ADRest's errors mails.
    #: Set NOTIFY_ERRORS = None for disable this functionality
    "NOTIFY_ERRORS": [500],

    # List of errors notifiers
    "NOTIFIERS": ["adrest.utils.notifiers.email_notifier"],

    #: Set maximum requests per timeframe
    "THROTTLE_AT": 120,

    #: Set timeframe length
    "THROTTLE_TIMEFRAME": 60,

    #: We do not restrict access for OPTIONS request.
    "ALLOW_OPTIONS": False,

    #: Template path for ADRest map
    "MAP_TEMPLATE": 'api/map.html',

    #: Logger name
    "LOGGER_NAME": "api.errors"
    }


ADREST_CONFIG.update(getattr(settings, 'ADREST', {}))

NOTIFIERS = get_notifiers(ADREST_CONFIG['NOTIFIERS'])
