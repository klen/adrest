""" Setup ADRest. """
import re
import sys
from os import path as op, walk

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


_read = lambda f: open(
    op.join(op.dirname(__file__), f)).read() if op.exists(f) else ''

_meta = _read('adrest/__init__.py')
_license = re.search(r'^__license__\s*=\s*"(.*)"', _meta, re.M).group(1)
_project = re.search(r'^__project__\s*=\s*"(.*)"', _meta, re.M).group(1)
_version = re.search(r'^__version__\s*=\s*"(.*)"', _meta, re.M).group(1)

install_requires = [
    l for l in _read('requirements.txt').split('\n')
    if l and not l.startswith('#')]

tests_require = [
    l for l in _read('requirements-tests.txt').split('\n')
    if l and not l.startswith('#')]

package_data = []

for folder in ['templates']:
    for root, dirs, files in walk(op.join(_project, folder)):
        for filename in files:
            package_data.append("%s/%s" % (root[len(_project) + 1:], filename))


class __PyTest(TestCommand):

    test_args = []
    test_suite = True

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    author_email='horneds@gmail.com',
    author='Kirill Klenov',
    description=_read('DESCRIPTION'),
    install_requires=install_requires,
    license=_license,
    long_description=_read('README.rst'),
    name=_project,
    package_data={'': package_data},
    packages=find_packages(),
    platforms=('Any'),
    keywords='rest rpc api django'.split(),
    tests_require=tests_require,
    cmdclass={'test': __PyTest},
    url=' http://github.com/klen/{0}'.format(_project),
    version=_version,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)', # noqa
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)

# pylama:ignore=E731
