version_info = (1, 0, 5)

__version__ = version = '.'.join(map(str, version_info))
__project__ = PROJECT = __name__
__author__ = AUTHOR = "Kirill Klenov <horneds@gmail.com>"
__license__ = LICENSE = "GNU LGPL"


# Preload ADREST tags
from django.template import builtins
from .templatetags import register

builtins.append(register)
