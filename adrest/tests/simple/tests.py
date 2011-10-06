from adrest.tests.utils import AdrestTestCase
from adrest.tests.simple.api import API, TaskResource


class SimpleTestCase(AdrestTestCase):
    api = API

    def test_base(self):
        response = self.get_resource(TaskResource)
        self.assertContains(response, 'true')
