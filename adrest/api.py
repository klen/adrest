""" Implement API. """
import logging

from django.conf.urls.defaults import patterns
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

    def register(self, resource, **meta):
        """ Add resource to the API.

        :param resource: Resource class for registration
        :param **meta: Redefine Meta options for the resource

        :return adrest.views.Resource: Generated resource.

        """

        # Must be instance of ResourceView
        assert issubclass(resource, ResourceView), \
            "{0} not subclass of ResourceView".format(resource)

        # Cannot be abstract
        assert not resource._meta.abstract, \
            "Attempt register of abstract resource: {0}.".format(resource)

        # Fabric of resources
        meta = dict(self.meta, **meta)
        meta['name'] = meta.get('name', resource._meta.name)
        options = type('Meta', tuple(), meta)

        params = dict(api=self, Meta=options, **meta)

        params['__module__'] = '%s.%s' % (
            self.prefix, self.str_version.replace('.', '_'))

        params['__doc__'] = resource.__doc__

        resource = type('%s%s' % (
            resource.__name__, len(self.resources)), (resource,), params)

        if self.resources.get(resource._meta.url_name):
            logger.warning(
                "A resource '%r' is replacing the existing record for '%s'",
                resource, self.resources.get(resource._meta.url_name))

        self.resources[resource._meta.url_name] = resource
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
        if not name in self.resources:
            raise exceptions.HttpError('Unknown method \'%s\'' % name,
                                       status=status.HTTP_501_NOT_IMPLEMENTED)
        request = request or HttpRequest()
        resource = self.resources[name]
        view = resource.as_view(api=self)
        return view(request, **params)

# lint_ignore=W0212
