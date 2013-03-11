#!/usr/bin/env python
import os

from setuptools import setup, find_packages

from adrest import version, PROJECT, LICENSE


PACKAGE_DATA = []

for folder in ['templates']:
    for root, dirs, files in os.walk(os.path.join(PROJECT, folder)):
        for filename in files:
            PACKAGE_DATA.append("%s/%s" % (root[len(PROJECT) + 1:], filename))


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''

install_requires = read('requirements.txt').split()

setup(
    author_email='horneds@gmail.com',
    author='Kirill Klenov',
    description=read('DESCRIPTION'),
    install_requires=install_requires,
    license=LICENSE,
    long_description=read('README.rst'),
    name=PROJECT,
    package_data={'': PACKAGE_DATA},
    packages=find_packages(),
    platforms=('Any'),
    tests_require=['pymongo', 'milkman'],
    test_suite='tests.run_tests',
    url=' http://github.com/klen/{0}'.format(PROJECT),
    version=version,
)
