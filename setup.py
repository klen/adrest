""" Setup ADRest. """
import os

from setuptools import setup, find_packages, Command

from adrest import version, PROJECT, LICENSE


PACKAGE_DATA = []

for folder in ['templates']:
    for root, dirs, files in os.walk(os.path.join(PROJECT, folder)):
        for filename in files:
            PACKAGE_DATA.append("%s/%s" % (root[len(PROJECT) + 1:], filename))


def __read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

install_requires = __read('requirements.txt').split()


class PyTest(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys,subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)

setup(
    author_email='horneds@gmail.com',
    author='Kirill Klenov',
    description=__read('DESCRIPTION'),
    install_requires=install_requires,
    license=LICENSE,
    long_description=__read('README.rst'),
    name=PROJECT,
    package_data={'': PACKAGE_DATA},
    packages=find_packages(),
    platforms=('Any'),
    keywords='rest rpc api django'.split(),
    tests_require=['pytest', 'pymongo', 'mixer'],
    cmdclass={ 'test': PyTest },
    url=' http://github.com/klen/{0}'.format(PROJECT),
    version=version,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)', # nolint
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
