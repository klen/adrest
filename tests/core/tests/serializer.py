from django.test import TestCase
from mixer.backend.django import mixer


class CoreSerializerTest(TestCase):

    def setUp(self):
        for _ in range(1, 10):
            mixer.blend('main.book')

    def test_base_types(self):
        """ Testing serialization of base types.
        """
        from adrest.utils.serializer import BaseSerializer
        try:
            from collections import OrderedDict
        except ImportError:
            from ordereddict import OrderedDict # noqa

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

        pirate = mixer.blend('core.pirate', name='Billy')
        data = [
            mixer.blend('core.boat', pirate=pirate),
            mixer.blend('core.boat', pirate=pirate),
            28, 'string']

        serializer = BaseSerializer(
            exclude='fake',
            include='pk',
            related=dict(
                pirate=dict(fields='character')
            ),
        )
        self.assertEqual(serializer.model_options['exclude'], set(['fake']))

        out = serializer.to_simple(data, **serializer.model_options)
        self.assertTrue(out[0]['fields']['pk'])
        self.assertEqual(out[0]['fields']['pirate']['fields']['character'],
                         data[0].pirate.character)

        # Test m2o serialization
        serializer = BaseSerializer(
            include="boat_set",
            related=dict(
                boat_set=dict(
                    fields=[])
            ),
        )
        out = serializer.to_simple(pirate, **serializer.model_options)

        self.assertEquals(len(out['fields']['boat_set']), 2)
        for boat in out['fields']['boat_set']:
            self.assertEquals(boat['fields']['pirate'], pirate.pk)
            self.assertTrue('title' in boat['fields'].keys())

        out = serializer.to_simple(pirate)
        self.assertTrue('model' in out)

        out = serializer.to_simple(pirate, include=['boat_set'])
        self.assertTrue(out['fields']['boat_set'])
        self.assertEqual(len(list(out['fields']['boat_set'])), 2)

    def test_paginator(self):
        from adrest.mixin import EmitterMixin
        from django.views.generic import View
        from django.test import RequestFactory
        from tests.core.models import Pirate
        from adrest.utils.paginator import Paginator

        mixer.cycle(3).blend('core.pirate')

        class SomeResource(EmitterMixin, View):

            class Meta:
                model = 'core.pirate'
                dyn_prefix = 'adr-'
                limit_per_page = 2

            def dispatch(self, request, **resources):
                p = Paginator(request, self, Pirate.objects.all())
                return self.emit(p, request=request)

        rf = RequestFactory()
        resource = SomeResource()

        response = resource.dispatch(rf.get('/'))
        self.assertContains(response, '"page": 1')
        self.assertContains(response, '"num_pages": 2')

    def test_xml(self):
        from adrest.utils.serializer import XMLSerializer
        from ...main.models import Book

        for _ in range(1, 10):
            mixer.blend(Book)
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
        self.assertTrue('":{"' in test)
