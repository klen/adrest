""" Test ADRest API module. """
from django.test import TestCase, RequestFactory

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

        api.register(Resource2, name='wow')
        resource = api.resources.get('wow')
        self.assertEqual(resource._meta.emitters, (XMLEmitter,))
        self.assertEqual(resource._meta.name, 'wow')

    def test_register(self):
        """ Test register method. """
        from adrest.api import Api

        api = Api('1.0.0')

        class TestResource(ResourceView):

            class Meta:
                name = 'test1'

        api.register(TestResource, name='test2')
        resource = api.resources.get('test2')
        self.assertEqual(resource._meta.name, 'test2')

        @api.register
        class TestResource(ResourceView):

            class Meta:
                name = 'test3'

        self.assertTrue('test3' in api.resources)

        @api.register()
        class TestResource(ResourceView):

            class Meta:
                name = 'test4'

        self.assertTrue('test4' in api.resources)

        @api.register(name='test6')
        class TestResource(ResourceView):

            class Meta:
                name = 'test5'

        self.assertFalse('test5' in api.resources)
        self.assertTrue('test6' in api.resources)

    def test_fabric(self):
        from adrest.api import Api

        api = Api('1.0.0')

        @api.register
        class PirateResource(ResourceView):

            class Meta:
                model = 'core.pirate'

            def get_collection(self, request, **resources):
                return super(PirateResource, self).get_collection(
                    request, **resources)

        resource = api.resources['pirate']
        rf = RequestFactory()
        response = resource().dispatch(rf.get('/'))
        self.assertContains(response, 'resources')

    def test_version(self):
        """ Test version. """
        from ..api import api2

        resource = api2.resources.get('pirate')
        self.assertEqual(resource.api, api2)

        uri = api2.testCase.reverse('pirate')
        self.assertEqual(uri, '/pirates2/1.0.0/pirate/')



# lint_ignore=E0102,W0404,C0110
