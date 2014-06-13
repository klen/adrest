"""
You can use :class:`adrest.Api` for bind multiple :class:`adrest.ResourceView`
together with version prefix.

Create API
----------

Default use: ::

    from adrest.api import Api
    from myresources import Resource1, Resource2

    api = Api('0.1')


Register a resource
-------------------
After creation you can register some resources with that Api. ::

    api.register(Resource1)
    api.register(Resource2)

You can use `api.register` method as decorator: ::

    @api.register
    class SomeResource():
        ...


Enable API Map
--------------

You can enable API Map for quick reference on created resources. Use `api_map`
param. ::

    api = Api('1.0b', api_map=True)

By default access to map is anonimous. If you want use a custom authenticator
register map resource by manualy. ::

    from adrest.resources.map import MapResource

    api = Api('1.0')
    api.register(MapResource, authenticators=UserLoggedInAuthenticator)


Auto JSONRPC from REST
----------------------

If you are created some REST api with adrest, you already have JSON RPC too.
Use `api_rpc` param. ::

    api = Api('1.0', api_rpc=True)


"""
import logging

from django.conf.urls import patterns
from django.dispatch import Signal
from django.http import HttpRequest

from .resources.map import MapResource
from .resources.rpc import AutoJSONRPC
from .views import ResourceView
from .utils import exceptions, status, emitter


__all__ = 'Api',


logger = logging.getLogger('adrest')


class Api(object):

    """ Implements a registry to tie together resources that make up an API.

    Especially useful for navigation, providing multiple versions of your
    API.

    :param version: Version info as string or iterable.
    :param api_map: Enable :ref:`apimap`
    :param api_prefix: Prefix for URL and URL-name
    :param api_rpc: Enable :ref:`jsonrpc`
    :param **meta: Redefine Meta options for resource classes

    """

    def __init__(self, version=None, api_map=True, api_prefix='api',
                 api_rpc=False, **meta):
        self.version = self.str_version = version
        self.prefix = api_prefix
        self.resources = dict()
        self.request_started = Signal()
        self.request_finished = Signal()

        if not isinstance(self.str_version, basestring):
            try:
                self.str_version = '.'.join(map(str, version or list()))
            except TypeError:
                self.str_version = str(version)

        self.meta = dict()

        if api_map:
            self.register(MapResource)

        if api_rpc:
            self.register(AutoJSONRPC, emitters=[
                emitter.JSONPEmitter, emitter.JSONEmitter
            ])

        self.meta = meta

    def __str__(self):
        return self.str_version

    def register(self, resource=None, **meta):
        """ Add resource to the API.

        :param resource: Resource class for registration
        :param **meta: Redefine Meta options for the resource

        :return adrest.views.Resource: Generated resource.

        """
        if resource is None:
            def wrapper(resource):
                return self.register(resource, **meta)
            return wrapper

        # Must be instance of ResourceView
        if not issubclass(resource, ResourceView):
            raise AssertionError("%s not subclass of ResourceView" % resource)

        # Cannot be abstract
        if resource._meta.abstract:
            raise AssertionError("Attempt register of abstract resource: %s."
                                 % resource)

        # Fabric of resources
        meta = dict(self.meta, **meta)
        meta['name'] = meta.get('name', resource._meta.name)
        options = type('Meta', tuple(), meta)

        params = dict(api=self, Meta=options, **meta)

        params['__module__'] = '%s.%s' % (
            self.prefix, self.str_version.replace('.', '_'))

        params['__doc__'] = resource.__doc__

        new_resource = type(
            '%s%s' % (resource.__name__, len(self.resources)),
            (resource,), params)

        if self.resources.get(new_resource._meta.url_name):
            logger.warning(
                "A resource '%r' is replacing the existing record for '%s'",
                new_resource, self.resources.get(new_resource._meta.url_name))

        self.resources[new_resource._meta.url_name] = new_resource

        return resource

    @property
    def urls(self):
        """ Provide URLconf details for the ``Api``.

        And all registered ``Resources`` beneath it.

            :return list: URL's patterns

        """
        urls = []

        for url_name in sorted(self.resources.keys()):

            resource = self.resources[url_name]
            urls.append(resource.as_url(
                api=self,
                name_prefix='-'.join(
                    (self.prefix, self.str_version)).strip('-'),
                url_prefix=self.str_version
            ))

        return patterns(self.prefix, *urls)

    def call(self, name, request=None, **params):
        """ Call resource by ``Api`` name.

        :param name: The resource's name (short form)
        :param request: django.http.Request instance
        :param **params: Params for a resource's call

        :return object: Result of resource's execution

        """
        if name not in self.resources:
            raise exceptions.HttpError(
                'Unknown method \'%s\'' % name,
                status=status.HTTP_501_NOT_IMPLEMENTED)
        request = request or HttpRequest()
        resource = self.resources[name]
        view = resource.as_view(api=self)
        return view(request, **params)

    @property
    def testCase(self):
        """ Generate class for testing this API.

        :return TestCase: A testing class

        """
        from adrest.tests import AdrestTestCase

        return type('TestCase', (AdrestTestCase, ), dict(api=self))
