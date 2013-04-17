from django.test import TestCase
from milkman.dairy import milkman


class SerializerTest(TestCase):

    def setUp(self):
        for _ in range(1, 10):
            milkman.deliver('main.book')

    def test_base_types(self):
        """ Testing serialization of base types.
        """
        from adrest.utils.serializer import BaseSerializer
        try:
            from collections import OrderedDict
        except ImportError:
            from ordereddict import OrderedDict # nolint

        from datetime import datetime
        from decimal import Decimal

        serializer = BaseSerializer()
        data = dict(
            string_='test',
            unicode_=unicode('test'),
            datetime_=datetime(2007, 01, 01),
            odict_=OrderedDict(value=1),
            dict_=dict(
                list_=[1, 2.35, Decimal(3), False]
            )
        )

        value = serializer.serialize(data)
        self.assertEqual(value, dict(
            string_=u'test',
            unicode_=u'test',
            datetime_='2007-01-01T00:00:00',
            odict_=dict(value=1),
            dict_=dict(
                list_=[1, 2.35, 3.0, False]
            )
        ))

    def test_django_model(self):
        from adrest.utils.serializer import BaseSerializer
        user = milkman.deliver('auth.User', username="testusername")
        data = [
            milkman.deliver('simple.task', user=user),
            milkman.deliver('simple.task', user=user),
            28, 'string']

        serializer = BaseSerializer(
            exclude='fake',
            include='username',
            related=dict(
                user=dict(fields='email')
            ),
        )
        self.assertEqual(serializer.model_options['exclude'], set(['fake']))

        out = serializer.to_simple(data, **serializer.model_options)
        self.assertEqual(out[0]['fields']['username'], data[0].user.username)

        # Test m2o serialization
        serializer = BaseSerializer(
            include="task_set",
            related=dict(
                task_set=dict(
                    fields=[])
            ),
        )
        out = serializer.to_simple(user)

        self.assertEquals(len(out['fields']['task_set']), 2)
        for task in out['fields']['task_set']:
            self.assertEquals(task['fields']['user'], user.pk)
            self.assertTrue('title' in task['fields'].keys())

    def test_xml(self):
        from adrest.utils.serializer import XMLSerializer
        from ...main.models import Book
        for _ in range(1, 10):
            milkman.deliver(Book)
        worker = XMLSerializer()
        test = worker.serialize(Book.objects.all())
        self.assertTrue("author" in test)

    def test_json(self):
        from ...main.models import Author
        from adrest.utils.serializer import JSONSerializer
        authors = Author.objects.all()
        worker = JSONSerializer(options=dict(
            separators=(',', ':')
        ))
        test = worker.serialize(authors)
        self.assertTrue("main.author" in test)
        self.assertTrue('"fields":{"active":true,"name"' in test)
