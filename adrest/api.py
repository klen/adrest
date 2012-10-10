import logging

from django.conf.urls.defaults import patterns
from django.dispatch import Signal
from django.http import HttpRequest

from .resources.map import MapResource
from .resources.rpc import AutoJSONRPC
from .views import ResourceView
from .utils import exceptions, status, tools, emitter


LOG = logging.getLogger('adrest')


class Api(object):

    """ Implements a registry to tie together the various resources that make up
        an API.

        Especially useful for navigation, providing multiple versions of your API.

        :param version: Version info as string or iterable.
        :param api_map: Enable API map (true by default)
        :param api_prefix: API Url prefix ('api' by default)
        :param api_rpc: Enable automatic Json RPC (default false)

        Additional params will be putted in self resources.

    """
    def __init__(self, version=None, api_map=True, api_prefix='api', api_rpc=False, **params):
        self.version = self.str_version = version
        self.prefix = api_prefix
        self.params = params
        self.resources = dict()
        self.request_started = Signal()
        self.request_finished = Signal()

        if api_map:
            self.resources[MapResource.meta.url_name] = MapResource

        # Enable Auto JSON RPC resource
        if api_rpc:
            self.resources[AutoJSONRPC.meta.url_name] = AutoJSONRPC
            self.params['emitters'] = tools.as_tuple(params.get('emitters', [])) + (
                emitter.JSONPEmitter, emitter.JSONEmitter
            )

        if not isinstance(self.str_version, basestring):
            try:
                self.str_version = '.'.join(map(str, version or list()))
            except TypeError:
                self.str_version = str(version)

    def __str__(self):
        return self.str_version

    def register(self, resource, **params):
        """ Registers resource for the API.

            :param resource: Resource class for registration

            Additional params will be putted in the resource.
        """

        # Must be instance of ResourceView
        assert issubclass(resource, ResourceView), "%s not subclass of ResourceView" % resource

        # Fabric of resources
        params = dict(self.params, **params)
        if params:
            params['name'] = ''.join(bit for bit in resource.__name__.split(
                'Resource') if bit).lower()

            params['__module__'] = '%s.%s' % (
                self.prefix, self.str_version.replace('.', '_'))

            params['__doc__'] = resource.__doc__

            resource = type('%s%s' % (
                resource.__name__, len(self.resources)), (resource,), params)

        if self.resources.get(resource.meta.url_name):
            LOG.warning("A new resource '%r' is replacing the existing record for '%s'" % (resource, self.resources.get(resource.url_name)))

        self.resources[resource.meta.url_name] = resource

    @property
    def urls(self):
        """ Provides URLconf details for the ``Api`` and all registered
            ``Resources`` beneath it.
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
        """
        if not name in self.resources:
            raise exceptions.HttpError('Unknown method \'%s\'' % name,
                                       status=status.HTTP_501_NOT_IMPLEMENTED)
        request = request or HttpRequest()
        resource = self.resources[name]
        view = resource.as_view(api=self)
        return view(request, **params)
