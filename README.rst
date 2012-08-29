ADREST
######

Adrest is Another Django REST. Django application for simple make HTTP REST API.

Documentation in construction.

.. image:: https://secure.travis-ci.org/klen/adrest.png?branch=develop
    :target: http://travis-ci.org/klen/adrest
    :alt: Build Status

Examples: ::

    from adrest.api import Api
    from adrest.views import ResourceView

    class BookResource(ResourceView):
        allowed_methods = 'get', 'post'
        model = 'books.book'

    api = Api(version(1, 0, 0))
    api.register(BookResource)

    urlpatterns = api.urls

    


Requirements
=============

- python >= 2.6
- django >= 1.4.0


Installation
=============

**Adrest** should be installed using pip: ::

    pip install adrest


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


Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/adrest/issues


Contributing
============

Development of adrest happens at github: https://github.com/klen/adrest


Contributors
=============

* klen_ (Kirill Klenov)


License
=======

Licensed under a `GNU lesser general public license`_.


.. _GNU lesser general public license: http://www.gnu.org/copyleft/lesser.html
.. _klen: http://klen.github.com/
