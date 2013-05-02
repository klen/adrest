from milkman.dairy import milkman

from ..api import api as API
from adrest.tests import AdrestTestCase
from adrest.views import ResourceView


class CoreResourceTest(AdrestTestCase):

    api = API

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

    def test_resources(self):

        pirate = milkman.deliver('core.pirate')
        for _ in xrange(3):
            milkman.deliver('core.boat', pirate=pirate)

        self.assertEqual(pirate.boat_set.count(), 3)

        self.delete_resource('pirate-boat', pirate=pirate, data=dict(
            boat=[b.pk for b in pirate.boat_set.all()[:2]]
        ))
        self.assertEqual(pirate.boat_set.count(), 1)

# lint_ignore=F0401
