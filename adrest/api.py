import logging

from django.conf.urls.defaults import url


LOG = logging.getLogger('adrest')


class Api(object):
    """ Implements a registry to tie together the various resources that make up
        an API.

        Especially useful for navigation, HATEOAS and for providing multiple
        versions of your API.
    """
    def __init__(self, version, **kwargs):
        self.version = version
        self.kwargs = kwargs
        try:
            self.str_version = '.'.join(map(str, version))
        except TypeError:
            self.str_version = str(version)

        self._resources = dict()

    def register(self, resource, uri=None, name=None, **kwargs):
        """ Register resource subclass with API.
        """
        key = name or resource.get_urlname()

        if self._resources.get(key):
            LOG.warning("A new resource '%r' is replacing the existing record for '%s'" % (resource, key))

        self._resources[key] = dict(
                resource=resource,
                uri=uri or resource.get_urlregex(),
                name=name,
                kwargs=kwargs )

    @property
    def urls(self):
        """ Provides URLconf details for the ``Api`` and all registered
            ``Resources`` beneath it.
        """
        patterns = []
        for key in sorted(self._resources.keys()):

            value = self._resources[key]

            # Resource
            resource = value['resource']

            # Params
            params = dict()
            params.update(self.kwargs)
            params.update(value['kwargs'])

            # URL
            name = 'api-%s-%s' % ( self.str_version, key)
            uri = '^%s/%s' % ( self.str_version, value['uri'])
            view = resource.as_view(api=self, **params)
            patterns.append(url(uri, view, name=name))

        return patterns
