""" Build docs. """
import os
import sys
import datetime

from adrest import __version__ as release

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx']
source_suffix = '.rst'
master_doc = 'index'
project = u'ADRest'
copyright = u'%s, Kirill Klenov' % datetime.datetime.now().year
version = '.'.join(release.split('.')[:2])
exclude_patterns = ['_build']
html_use_modindex = False
htmlhelp_basename = 'ADRestdoc'
man_pages = [
    ('index', 'adrest', u'ADRest Documentation', [u'Kirill Klenov'], 1)
]
pygments_style = 'tango'

# lint_ignore=W0622
