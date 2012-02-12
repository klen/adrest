from adrest.tests.utils import AdrestTestCase
from .simple.api import API


class SimpleTestCase(AdrestTestCase):
    api = API

    def test_base(self):
        response = self.get_resource('task')
        self.assertContains(response, 'true')
