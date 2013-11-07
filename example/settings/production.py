""" Production's settings.
"""
from .core import * # nolint

# Hack for adrest loading in example project
import sys
sys.path.insert(0, op.abspath(op.dirname(op.dirname(op.dirname(__file__)))))


ENVIRONMENT_NAME = 'production'

# Applications
INSTALLED_APPS += (

    # Community apps
    'south',

    # Base project app
    'main',

    # API
    'adrest',

)

# Caches
CACHES['default']['KEY_PREFIX'] = '_'.join((PROJECT_NAME, 'PRJ'))

# Sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

# Templates cache
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', TEMPLATE_LOADERS),
)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    }
}

logging.info('Production settings are loaded.')
