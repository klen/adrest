from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class AdrestTestCase(TestCase):
    api = None

    def setUp(self):
        assert self.api, "API must be defined"
        self.client = Client()

    def reverse(self, resource, **kwargs):
        return reverse('api-%s-%s' % (str(self.api), resource.meta.urlname), kwargs=kwargs)
