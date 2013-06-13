"""
    **ADRest** is an API framework for Django. It supports REST_ and RPC_
    paradigms.

    :copyright: 2013 by Kirill Klenov.
    :license: BSD, see LICENSE for more details.
"""
version_info = (3, 0, 1)

__version__ = version = '.'.join(map(str, version_info))
__project__ = PROJECT = __name__
__author__ = AUTHOR = "Kirill Klenov <horneds@gmail.com>"
__license__ = LICENSE = "GNU LGPL"

try:
    from django.conf import settings as django_settings # nolint
    if django_settings.configured:

        if not 'adrest' in django_settings.INSTALLED_APPS:
            import logging
            logging.warn('You should added "adrest" to INSTALLED_APPS.')

except ImportError:
    pass

# lint_ignore=W402
