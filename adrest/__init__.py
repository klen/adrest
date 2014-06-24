""" **ADREST** is an API framework for Django.

It supports REST_ and RPC_ paradigms.

:copyright: 2013 by Kirill Klenov.
:license: BSD, see LICENSE for more details.

"""

__version__ = "3.2.3"
__project__ = "adrest"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "GNU LGPL"

version_info = [p for p in map(int, __version__.split("."))]

try:
    from django.conf import settings as django_settings
    if django_settings.configured:

        if 'adrest' not in django_settings.INSTALLED_APPS:
            import logging
            logging.warn('You should added "adrest" to INSTALLED_APPS.')

except ImportError:
    pass
