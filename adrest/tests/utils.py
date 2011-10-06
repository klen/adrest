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
        kwargs = dict((k, getattr(v, "pk", v)) for k, v in kwargs.iteritems())
        name_ver = '' if not str(self.api) else '%s-' % str(self.api)
        return reverse('api-%s%s' % (name_ver, resource.meta.urlname), kwargs=kwargs)

    def get_resource(self, resource, method='get', data=None, key=None, **kwargs):
        uri = self.reverse(resource, **kwargs)
        method = getattr(self.client, method)
        if isinstance(key, Model):
            key = key.key
        return method(uri, data=data or dict(), HTTP_AUTHORIZATION=key)

    put_resource = curry(get_resource, method='put')
    post_resource = curry(get_resource, method='post')
    delete_resource = curry(get_resource, method='delete')
