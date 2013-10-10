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

from adrest.utils.tools import import_functions


ADREST_CONFIG = {
    # Handlers for API logs.
    "LOG_HANDLERS": ["adrest.utils.log_handlers.db_handler", ],

    #: Make abstract model to create custom models
    "ABSTRACT_ACCESS_KEY": False,

    #: Make abstract `adrest.models.AccessKey`
    "ABSTRACT_ACCESS": False,

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

# Backward compatibility with old versions
for key in filter(lambda x: x.startswith("ADREST_"), dir(settings)):
    ADREST_CONFIG[key[7:]] = getattr(settings, key, None)

ADREST_CONFIG.update(getattr(settings, 'ADREST', {}))

NOTIFIERS = import_functions(ADREST_CONFIG['NOTIFIERS'])

LOG_HANDLERS = import_functions(ADREST_CONFIG['LOG_HANDLERS'])
