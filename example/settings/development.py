""" Development related settings.
"""
from .production import * # nolint
from .core import TEMPLATE_LOADERS

assert TEMPLATE_LOADERS

ENVIRONMENT_NAME = 'development'

# Caches
CACHES['default']['KEY_PREFIX'] = '_'.join((PROJECT_NAME, 'DEV'))

# Debug
DEBUG = True
TEMPLATE_DEBUG = True
if DEBUG:
    INTERNAL_IPS += tuple('192.168.1.%s' % x for x in range(1, 111))
    TEMPLATE_CONTEXT_PROCESSORS += 'django.core.context_processors.debug',
    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware', )
    INSTALLED_APPS += ('debug_toolbar', )
    DEBUG_TOOLBAR_CONFIG = dict(INTERCEPT_REDIRECTS=False)

# Logging
LOGGING['loggers']['django.request']['level'] = 'DEBUG'
LOGGING['loggers']['celery']['level'] = 'DEBUG'
logging.info('Development settings are loaded.')
