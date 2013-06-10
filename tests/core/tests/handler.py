from django.db import models
from django.views.generic import View
from mixer.backend.django import mixer

from adrest.mixin import HandlerMixin
from adrest.tests import AdrestTestCase
from ..api import api as API


class CoreHandlerTest(AdrestTestCase):

    api = API

    def test_meta_model(self):

        class Resource(View, HandlerMixin):

            class Meta:
                model = 'core.pirate'

        self.assertTrue(issubclass(Resource._meta.model, models.Model))

    def test_meta_name(self):

        class Resource(View, HandlerMixin):

            class Meta:
                model = 'core.pirate'

        self.assertEqual(Resource._meta.name, 'pirate')

        class IslandResource(View, HandlerMixin):

            class Meta:
                name = 'map'
                model = 'core.island'

        self.assertEqual(IslandResource._meta.name, 'map')

        class TreasureResource(View, HandlerMixin):

            class Meta:
                parent = Resource
                model = 'core.treasure'

        self.assertEqual(TreasureResource._meta.name, 'treasure')

    def test_methods(self):

        for _ in xrange(3):
            pirate = mixer.blend('core.pirate', character='good')

        response = self.get_resource('pirate')
        self.assertContains(response, '"count": 3')

        response = self.post_resource('pirate', data=dict(
            name='John',
            character='evil',
        ))
        self.assertContains(response, '"name": "John"')

        john = response.response
        response = self.put_resource('pirate', pirate=john, data=dict(
            name='Billy'
        ))
        self.assertContains(response, '"name": "Billy"')
        billy = response.response
        self.assertEqual(john, billy)

        response = self.delete_resource('pirate', pirate=billy)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(billy).objects.filter(name='Billy').count(), 0)

        response = self.patch_resource('pirate', data=dict(
            pirate=[1, 2],
            name='Tom'
        ))
        self.assertEqual(len(response.response), 2)

        for pirate in response.response:
            self.assertEqual(pirate.name, 'Tom')
            self.assertTrue(pirate.pk in [1, 2])


# lint_ignore=F0401,C
