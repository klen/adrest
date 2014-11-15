|logo| ADREST
#############

Adrest is Another Django REST. Django application for simple make HTTP REST API.

Documentation in `construction <http://adrest.readthedocs.org>`_.

.. _badges:

.. image:: http://img.shields.io/travis/klen/adrest.svg?style=flat-square
    :target: http://travis-ci.org/klen/adrest
    :alt: Build Status

.. image:: http://img.shields.io/coveralls/klen/adrest.svg?style=flat-square
    :target: https://coveralls.io/r/klen/adrest
    :alt: Coverals

.. image:: http://img.shields.io/pypi/v/adrest.svg?style=flat-square
    :target: https://pypi.python.org/pypi/adrest
    :alt: Version

.. image:: http://img.shields.io/pypi/dm/adrest.svg?style=flat-square
    :target: https://pypi.python.org/pypi/adrest
    :alt: Downloads

.. image:: http://img.shields.io/pypi/l/adrest.svg?style=flat-square
    :target: https://pypi.python.org/pypi/adrest
    :alt: License

.. image:: http://img.shields.io/gratipay/klen.svg?style=flat-square
    :target: https://www.gratipay.com/klen/
    :alt: Donate

.. _requirements:
    
Requirements
=============

- Python 2.7
- Django (1.5, 1.6, 1.7)

.. _installation:

Installation
=============

**ADRest** should be installed using pip: ::

    pip install adrest

.. _quickstart:

Quick start
===========
::

    from adrest import Api, ResourceView

    api = Api('v1')

    @api.register
    class BookResource(ResourceView):
        class Meta:
            allowed_methods = 'get', 'post'
            model = 'app.book'

    urlpatterns = api.urls


.. _setup:

Setup
=====

Adrest settings (default values): ::

    # Enable logs
    ADREST_ACCESS_LOG = False

    # Auto create adrest access key for User
    ADREST_AUTO_CREATE_ACCESSKEY = False

    # Max resources per page in list views
    ADREST_LIMIT_PER_PAGE = 50

    # Display django standart technical 500 page
    ADREST_DEBUG = False

    # Limit request number per second from same identifier, null is not limited
    ADREST_THROTTLE_AT = 120
    ADREST_THROTTLE_TIMEFRAME = 60

    # We do not restrict access for OPTIONS request
    ADREST_AUTHENTICATE_OPTIONS_REQUEST = False

.. note::
    Add 'adrest' to INSTALLED_APPS


Use adrest
==========

See test/examples in ADREST sources.


.. _bagtracker:

Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/adrest/issues


.. _contributing:

Contributing
============

Development of adrest happens at github: https://github.com/klen/adrest


.. _contributors:

Contributors
=============

* klen_ (Kirill Klenov)


.. _license:

License
=======

Licensed under a `GNU lesser general public license`_.


.. _links:

.. _GNU lesser general public license: http://www.gnu.org/copyleft/lesser.html
.. _klen: http://klen.github.com/
.. _REST: http://en.wikipedia.org/wiki/Representational_state_transfer
.. _RPC: http://en.wikipedia.org/wiki/JSON-RPC
.. |logo| image:: https://raw.github.com/klen/adrest/develop/docs/_static/logo.png
                  :width: 100
