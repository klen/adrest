""" Create Django project for testing. """

from django.conf import settings

# Configure Django
settings.configure(
    ADMINS=('test', 'test@test.com'),

    ROOT_URLCONF='tests.core.urls',
    DEBUG=True,

    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'USER': '',
            'PASSWORD': '',
            'TEST_CHARSET': 'utf8',
        }
    },
    CACHE_BACKEND='locmem://',

    INSTALLED_APPS=(
        'django.contrib.contenttypes',
        'django.contrib.auth',
        'adrest',
        'tests.core', 'tests.main', 'tests.rpc',
    ),

    TEMPLATE_DEBUG=True,
    TEMPLATE_CONTEXT_PROCESSORS=(
        'django.core.context_processors.static',
        'django.core.context_processors.request',
        'django.contrib.auth.context_processors.auth',
    ),

    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',

    ADREST_ACCESS_LOG=True,
    ADREST_ALLOW_OPTIONS=True,
    ADREST_MAIL_ERRORS=(500, 400),
    ADREST_AUTO_CREATE_ACCESSKEY=True,
)

# Django 1.7
from django import VERSION

if VERSION >= (1, 7):
    from django.apps import apps

    apps.populate(settings.INSTALLED_APPS)


# Setup tests
from django.core.management import call_command
call_command('syncdb', interactive=False)

from .core.tests import * # noqa
from .main.tests import * # noqa
from .rpc.tests import * # noqa

# lint_ignore=W0614,W0401,E272
