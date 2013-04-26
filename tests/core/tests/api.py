from django.test import TestCase
from adrest.views import ResourceView


class CoreApiTest(TestCase):

    def test_base(self):
        from adrest.api import Api

        api = Api('1.0.0')
        self.assertEqual(api.version, '1.0.0')
        self.assertTrue(api.urls)

        class Resource(ResourceView):
            model = 'core.pirate'

        api.register(Resource)
        self.assertEqual(len(api.urls), 2)
        self.assertTrue(api.resources.get('pirate'))

        class TreasureResource(ResourceView):
            model = 'core.treasure'
            parent = Resource

        api.register(TreasureResource)
        self.assertEqual(len(api.urls), 3)
        self.assertTrue(api.resources.get('pirate-treasure'))

        class PrefixResource(TreasureResource):
            prefix = 'more'

        api.register(PrefixResource)
        self.assertEqual(len(api.urls), 4)
        self.assertTrue(api.resources.get('pirate-more-treasure'))
