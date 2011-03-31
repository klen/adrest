from django.conf.urls.defaults import url

from adrest.views import ResourceView


class Api(object):

    def __init__(self, version, **kwargs):
        self.version = version
        try:
            self.str_version = '.'.join(map(str, version))
        except TypeError:
            self.str_version = str(version)

        self._handlers = dict()

    def register(self, handler):
        self._handlers[handler.get_urlname()] = handler

    @property
    def urls(self):
        patterns = []
        for key in sorted(self._handlers.keys()):
            handler = self._handlers[key]
            regex = '^%s/%s' % ( self.str_version, handler.get_urlregex())
            name = 'api-%s-%s' % ( self.str_version, handler.get_urlname())
            view = ResourceView.as_view(handler = handler, api = self)
            patterns.append(url(regex, view, name=name))
        return patterns
