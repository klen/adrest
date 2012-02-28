import logging

from django.conf.urls.defaults import patterns
from django.dispatch import Signal

from .map import MapResource
from .views import ResourceView


LOG = logging.getLogger('adrest')


class Api(object):
    """ Implements a registry to tie together the various resources that make up
        an API.

        Especially useful for navigation, HATEOAS and for providing multiple
        versions of your API.
    """
    def __init__(self, version=None, api_map=True, api_prefix='api', **params):
        self.version = version
        self.prefix = api_prefix
        self.params = params
        self.resources = dict()
        self.request_started = Signal()
        self.request_finished = Signal()

        if api_map:
            self.resources[MapResource.meta.url_name] = MapResource

        try:
            self.str_version = '.'.join(map(str, version or list()))
        except TypeError:
            self.str_version = str(version)

    def register(self, resource, **params):
        " Register resource subclass with API. "

        # Must be instance of ResourceView
        assert issubclass(resource, ResourceView), "%s not subclass of ResourceView" % resource

        # Fabric of resources
        params = dict(self.params, **params)
        if params:
            params['name'] = ''.join(bit for bit in resource.__name__.split('Resource') if bit).lower()
            params['__module__'] = '%s.%s' % (self.prefix, self.str_version.replace('.', '_'))
            resource = type('%s%s' % (resource.__name__, len(self.resources)), (resource,), params)

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
                api = self,
                name_prefix = '-'.join((
                            self.prefix,
                            self.str_version,
                        )).strip('-'),
                url_prefix = self.str_version
            ))

        return patterns(self.prefix, *urls)

    def __str__(self):
        return self.str_version
