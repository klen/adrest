from milkman.dairy import milkman # nolint

from .api import API
from .models import Task
from adrest.tests.utils import AdrestTestCase


class SimpleTestCase(AdrestTestCase):
    api = API

    def test_base(self):
        self.assertEqual(self.api.str_version, '1.0b')

        uri = self.reverse('task')
        self.assertEqual(uri, '/simple/1.0b/task/')

        response = self.get_resource('task')
        self.assertContains(response, 'true')

        response = self.post_resource('task2', data=dict(title='new'))
        self.assertEqual(
            response.content,
            '{"api": "1.0b", "user": ["This field is required."]}')

        task = milkman.deliver(Task)
        response = self.get_resource('task2')
        self.assertContains(response, 'num_pages')
        self.assertContains(
            response,
            "{0} -- {1}".format(task.title, task.user.username))
