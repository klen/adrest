from .api import API
from adrest.tests.utils import AdrestTestCase


class SimpleTestCase(AdrestTestCase):
    api = API

    def test_base(self):
        uri = self.reverse('task')
        self.assertEqual(uri, '/simple/task/')
        response = self.get_resource('task')
        self.assertContains(response, 'true')
