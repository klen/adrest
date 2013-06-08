""" Test ADRest API module. """
from django.test import TestCase

from adrest.views import ResourceView
from adrest.utils.emitter import XMLEmitter


class CoreApiTest(TestCase):

    """ Test api. """

    def test_base(self):
        """ Test main functionality. """
        from adrest.api import Api

        api = Api('1.0.0')
        self.assertEqual(api.version, '1.0.0')
        self.assertTrue(api.urls)

        class Resource(ResourceView):

            class Meta:
                model = 'core.pirate'

        api.register(Resource)
        self.assertEqual(len(api.urls), 2)
        self.assertTrue(api.resources.get('pirate'))

        class TreasureResource(ResourceView):

            class Meta:
                parent = Resource
                model = 'core.treasure'

        api.register(TreasureResource)
        self.assertEqual(len(api.urls), 3)
        self.assertTrue(api.resources.get('pirate-treasure'))

        class PrefixResource(TreasureResource):
            class Meta:
                prefix = 'more'

        api.register(PrefixResource)
        self.assertEqual(len(api.urls), 4)
        self.assertTrue(api.resources.get('pirate-more-treasure'))

        class Resource2(ResourceView):

            class Meta:
                model = 'core.pirate'
                emitters = XMLEmitter

        resource = api.register(Resource2, name='wow')
        self.assertEqual(resource._meta.emitters, (XMLEmitter,))
        self.assertEqual(resource._meta.name, 'wow')
