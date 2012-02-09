import logging

from django.conf.urls.defaults import url
from adrest.views import ApiMapResource, ResourceView


LOG = logging.getLogger('adrest')


class Api(object):
    """ Implements a registry to tie together the various resources that make up
        an API.

        Especially useful for navigation, HATEOAS and for providing multiple
        versions of your API.
    """
    def __init__(self, version=None, show_map=True, **params):
        self.version = version
        self.show_map = show_map
        self.params = params
        self._map = dict()

        try:
            self.str_version = '.'.join(map(str, version or list()))
        except TypeError:
            self.str_version = str(version)

    def register(self, resource, urlregex=None, urlname=None, **params):
        " Register resource subclass with API "

        assert issubclass(resource, ResourceView), " Resource must have ResourceView type "

        urlname = urlname or resource.meta.urlname
        urlregex = urlregex or resource.meta.urlregex

        if self._map.get(resource.meta.urlname):
            LOG.warning("A new resource '%r' is replacing the existing record for '%s'" % (resource, urlname))

        # Resource fabric
        params = dict(self.params, **params)
        if params:
            params['name'] = ''.join(bit for bit in resource.__name__.split('Resource') if bit).lower()
            resource = type('%s%s' % (resource.__name__, len(self._map)), (resource,), params)

        self._map[urlname] = urlregex, resource

    @property
    def urls(self):
        """ Provides URLconf details for the ``Api`` and all registered
            ``Resources`` beneath it.
        """

        patterns = []
        url_vprefix = name_vprefix = ''

        if self.str_version:
            url_vprefix = '%s/' % self.str_version
            name_vprefix = '%s-' % self.str_version

        if self.show_map:
            patterns.append(
                # self top level map
                url(r"^%s$" % url_vprefix, ApiMapResource.as_view(api=self), name="api-%s%s" % (name_vprefix, ApiMapResource.meta.urlname)),
            )

        for urlname in sorted(self._map.keys()):

            urlregex, resource = self._map[urlname]

            patterns.append(url('^%s%s' % (url_vprefix, urlregex),
                        resource.as_view(api=self),
                        name='api-%s%s' % (name_vprefix, urlname)))

        return patterns

    def __str__(self):
        return self.str_version
