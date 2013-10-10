""" Prepare a Django project for tests. """
import sys

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
    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.static',
        'django.core.context_processors.request',
        'django.contrib.auth.context_processors.auth',
    ),

    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend',

    ADREST = dict(
        ACCESS_LOG=True,
        ALLOW_OPTIONS=True,
        NOTIFY_ERRORS=(500, 400),
        AUTO_CREATE_ACCESSKEY=True
        ),
    NOSE_ARGS = [
        '--verbosity=3',
        '--nologcapture',
        '--no-byte-compile',
        #    '--stop', # stop after first failure
           '--pdb-failures',
        #    '--logging-clear-handlers'
        ]
)

import sys
def runtests(*test_args):
    from django_nose.runner import NoseTestSuiteRunner
    tests_runner = NoseTestSuiteRunner()
    failures = tests_runner.run_tests(['tests.core.tests',
                                       'tests.main.tests',
                                       'tests.rpc.tests'])


    sys.exit(failures)

# lint_ignore=W0614,W0401,E272
