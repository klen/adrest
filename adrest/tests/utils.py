from django.core.urlresolvers import reverse
from django.db.models import Model
from django.test import TestCase, Client
from django.utils.functional import curry


class AdrestTestCase(TestCase):
    api = None

    def setUp(self):
        assert self.api, "API must be defined"
        self.client = Client()

    def reverse(self, resource, **kwargs):
        if isinstance(resource, basestring):
            assert self.api._map.get(resource), "Invalid resource name: %s" % resource
            urlname = self.api._map.get(resource)['urlname']
            resource = self.api._map.get(resource)['resource']

        else:
            urlname = resource.meta.urlname

        kwargs = dict((k, getattr(v, "pk", v)) for k, v in kwargs.iteritems())
        name_ver = '' if not str(self.api) else '%s-' % str(self.api)
        return reverse('api-%s%s' % (name_ver, urlname), kwargs=kwargs)

    def get_resource(self, resource, method='get', data=None, key=None, headers=None, **kwargs):
        uri = self.reverse(resource, **kwargs)
        method = getattr(self.client, method)
        if isinstance(key, Model):
            key = key.key
        headers = dict() if headers is None else headers
        headers['HTTP_AUTHORIZATION'] = key
        return method(uri, data=data or dict(), **headers)

    put_resource = curry(get_resource, method='put')
    post_resource = curry(get_resource, method='post')
    delete_resource = curry(get_resource, method='delete')
