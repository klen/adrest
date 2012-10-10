#!/usr/bin/env python
""" Settings to run library tests
"""
import logging
import sys
from os.path import dirname, abspath

from django.conf import settings as django_settings

from tests import settings


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%d.%m %H:%M:%S')

if not django_settings.configured:
    django_settings.configure(
        **dict([(x, getattr(settings, x)) for x in dir(settings) if x.isupper()]))


def run_tests(*test_args):
    from django.test.simple import DjangoTestSuiteRunner
    if not test_args:
        test_args = [
            'main',
            'simple',
            'rpc',
        ]
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    tests_runner = DjangoTestSuiteRunner(
        verbosity=1, interactive=True, failfast=False)
    failures = tests_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    run_tests(*sys.argv[1:])
