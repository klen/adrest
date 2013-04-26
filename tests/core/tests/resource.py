from django.test import TestCase

from adrest.views import ResourceView


class CoreResourceTest(TestCase):

    def test_meta(self):

        class AlphaResource(ResourceView):
            pass
        self.assertEqual(AlphaResource.meta.name, 'alpha')

        class BetaResource(ResourceView):
            name = 'beta'
        self.assertEqual(BetaResource.meta.name, 'beta')
        self.assertEqual(BetaResource.meta.url_name, 'beta')

        class GammaResource(ResourceView):
            name = 'gamma'
            parent = BetaResource

        self.assertEqual(GammaResource.meta.parents, [BetaResource])
        self.assertEqual(GammaResource.meta.name, 'gamma')
        self.assertEqual(GammaResource.meta.url_name, 'beta-gamma')
