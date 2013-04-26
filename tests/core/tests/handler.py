from django.db import models
from django.test import TestCase
from django.views.generic import View

from adrest.mixin import HandlerMixin


class CoreHandlerTest(TestCase):

    def test_meta_model(self):

        class Resource(View, HandlerMixin):
            model = 'core.pirate'

        self.assertTrue(issubclass(Resource.model, models.Model))

    def test_meta_name(self):

        class Resource(View, HandlerMixin):
            model = 'core.pirate'

        self.assertEqual(Resource.meta.name, 'pirate')

        class IslandResource(View, HandlerMixin):
            model = 'core.island'
            name = 'map'

        self.assertEqual(IslandResource.meta.name, 'map')

        class TreasureResource(View, HandlerMixin):
            parent = Resource
            model = 'core.treasure'

        self.assertEqual(TreasureResource.meta.name, 'treasure')
