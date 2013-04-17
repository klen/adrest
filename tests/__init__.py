#!/usr/bin/env python
""" Settings to run library tests
"""
import logging
import sys


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%d.%m %H:%M:%S')


from django.conf import settings as django_settings
django_settings.configure(
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
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'adrest',
        'tests.core', 'tests.main', 'tests.rpc', 'tests.simple'
    ),

    TEMPLATE_DEBUG=True,
    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.static',
        'django.core.context_processors.request',
        'django.contrib.auth.context_processors.auth',
    ),

    ADREST_ACCESS_LOG=True,
    ADREST_ALLOW_OPTIONS=True,
    ADREST_MAIL_ERRORS=(500, 400),
    ADREST_AUTO_CREATE_ACCESSKEY=True,
)


from django.test.simple import DjangoTestSuiteRunner
tests_runner = DjangoTestSuiteRunner(failfast=False)
sys.exit(tests_runner.run_tests(['core']))
