import logging

from django.conf.urls.defaults import url
from adrest.views import ApiMapResource


LOG = logging.getLogger('adrest')


class Api(object):
    """ Implements a registry to tie together the various resources that make up
        an API.

        Especially useful for navigation, HATEOAS and for providing multiple
        versions of your API.
    """
    def __init__(self, version=None, show_map=True, **kwargs):
        self.version = version
        self.show_map = show_map
        self.kwargs = kwargs
        try:
            self.str_version = '.'.join(map(str, version or list()))
        except TypeError:
            self.str_version = str(version)

        self._map = dict()

    def register(self, resource, urlregex=None, urlname=None, **kwargs):
        """ Register resource subclass with API.
        """
        urlname = urlname or resource.meta.urlname
        urlregex = urlregex or resource.meta.urlregex

        if self._map.get(urlname):
            LOG.warning("A new resource '%r' is replacing the existing record for '%s'" % (resource, urlname))

        self._map[urlname] = dict(resource=resource, urlregex=urlregex, urlname=urlname, kwargs=kwargs)

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

            resource_info = self._map[urlname]

            # Resource
            resource = resource_info['resource']

            # Params
            params = dict()
            params.update(self.kwargs)
            params.update(resource_info['kwargs'])

            # URL
            urlname = 'api-%s%s' % ( name_vprefix, urlname)
            urlregex = '^%s%s' % ( url_vprefix, resource_info['urlregex'])
            view = resource.as_view(api=self, **params)
            patterns.append(url(urlregex, view, name=urlname))

        return patterns

    def __str__(self):
        return self.str_version
