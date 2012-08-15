version_info = (1, 7, 0)

__version__ = version = '.'.join(map(str, version_info))
__project__ = PROJECT = __name__
__author__ = AUTHOR = "Kirill Klenov <horneds@gmail.com>"
__license__ = LICENSE = "GNU LGPL"


# Preloads ADREST tags
try:
    from django.template import builtins
    from .templatetags import register

    builtins.append(register)

except ImportError:
    pass
