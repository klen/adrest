:orphan:

Welcome to ADRest documentation
###############################


.. == logo ==
.. image:: _static/logo.png
    :width: 100


.. == badges ==
.. _badges:
.. include:: ../README.rst
    :start-after: .. _badges:
    :end-before: .. _requirements:


.. == description ==
.. _description:
.. automodule:: adrest


.. == requirements ==
.. _requirements:
.. include:: ../README.rst
    :start-after: .. _requirements:
    :end-before: .. _installation:


.. == installation ==
.. _installation:
.. include:: ../README.rst
    :start-after: .. _installation:
    :end-before: .. _quickstart:


.. == quickstart ==
.. _quickstart:
.. include:: ../README.rst
    :start-after: .. _quickstart:
    :end-before: .. _setup:

.. toctree::
   :maxdepth: 2

    configuration
    api
    changes


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


.. == budtracker ==
.. _budtracker:
.. include:: ../README.rst
    :start-after: .. _bagtracker:
    :end-before: .. _contributing:


.. == contributing ==
.. _contributing:
.. include:: ../README.rst
    :start-after: .. _contributing:
    :end-before: .. _contributors:


.. == contributors ==
.. _contributors:
.. include:: ../README.rst
    :start-after: .. _contributors:
    :end-before: .. _license:


.. == license ==
.. _license:
.. include:: ../README.rst
    :start-after: .. _license:
    :end-before: .. _links:


.. == links ==
.. _links:
.. include:: ../README.rst
    :start-after: .. _links:
