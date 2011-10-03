from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.utils.functional import curry


class AdrestTestCase(TestCase):
    api = None

    def setUp(self):
        assert self.api, "API must be defined"
        self.client = Client()

    def reverse(self, resource, **kwargs):
        return reverse('api-%s-%s' % (str(self.api), resource.meta.urlname), kwargs=kwargs)

    def get_resource(self, resource, method='get', data=None, key=None, **kwargs):
        uri = self.reverse(resource, **kwargs)
        method = getattr(self.client, method)
        return method(uri, data=data or dict(), HTTP_AUTHORIZATION=key)

    put_resource = curry(get_resource, method='put')
    post_resource = curry(get_resource, method='post')
    delete_resource = curry(get_resource, method='delete')
