from milkman.dairy import milkman # nolint

from .api import API
from .models import Task
from adrest.tests.utils import AdrestTestCase, TestCase


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


class SerializerTest(TestCase):

    def setUp(self):
        for _ in range(1, 10):
            milkman.deliver('main.book')

    def test_simply(self):
        from adrest.utils.serializer import BaseSerializer
        user = milkman.deliver('auth.User', username="testusername")
        data = [
            milkman.deliver(Task, user=user),
            milkman.deliver(Task, user=user),
            28, 'string']

        serializer = BaseSerializer(
            _exclude='fake', _include='username', user=dict(
                _fields='email'))
        self.assertEqual(serializer.options['_exclude'], set(['fake']))

        out = serializer.to_simple(data, **serializer.options)
        self.assertEqual(out[0]['fields']['username'], data[0].user.username)

        # Test m2o serialization
        serializer = BaseSerializer(_include="task_set", task_set=dict(
            _fields=[]))
        out = serializer.to_simple(user, **serializer.options)

        self.assertEquals(len(out['fields']['task_set']), 2)
        for task in out['fields']['task_set']:
            self.assertEquals(task['fields']['user'], user.pk)
            self.assertTrue('title' in task['fields'].keys())

    def test_xml(self):
        from adrest.utils.serializer import XMLSerializer
        from ..main.models import Book
        worker = XMLSerializer()
        test = worker.serialize(Book.objects.all())
        self.assertTrue("author" in test)

    def test_json(self):
        from ..main.models import Author
        from adrest.utils.serializer import JSONSerializer
        authors = Author.objects.all()
        worker = JSONSerializer()
        test = worker.serialize(authors)
        self.assertTrue("main.author" in test)

    def test_types(self):
        from adrest.utils.serializer import BaseSerializer
        from collections import OrderedDict
        from datetime import datetime

        serializer = BaseSerializer()
        data = dict(
            string_='test',
            unicode_=unicode('test'),
            datetime_=datetime(2007, 01, 01),
            odict_=OrderedDict(value=1),
        )

        value = serializer.serialize(data)
        self.assertEqual(value, dict(
            string_=u'test',
            unicode_=u'test',
            datetime_='2007-01-01T00:00:00',
            odict_=dict(value=1),
        ))
