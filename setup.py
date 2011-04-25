#!/usr/bin/env python
import os

from setuptools import setup, find_packages

from adrest import version, PROJECT, LICENSE


PACKAGE_DATA = []

for folder in ['templates']:
    for root, dirs, files in os.walk(os.path.join(PROJECT, folder)):
        for filename in files:
            PACKAGE_DATA.append("%s/%s" % ( root[len(PROJECT)+1:], filename ))


def read( fname ):
    try:
        return open( os.path.join( os.path.dirname( __file__ ), fname ) ).read()
    except IOError:
        return ''


META_DATA = dict(
    name=PROJECT,
    version=version,
    LICENSE=LICENSE,
    description=read( 'DESCRIPTION' ),
    long_description=read( 'README.rst' ),
    platforms=('Any'),

    author='Kirill Klenov',
    author_email='horneds@gmail.com',
    url=' http://github.com/klen/adrest',

    packages=find_packages(),
    package_data = { '': PACKAGE_DATA, },

    install_requires = ('mimeparse',),

)


if __name__ == "__main__":
    setup( **META_DATA )
