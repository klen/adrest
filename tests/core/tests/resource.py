from mixer.backend.django import mixer

from ..api import api as API
from adrest.tests import AdrestTestCase
from adrest.views import ResourceView


class CoreResourceTest(AdrestTestCase):

    api = API

    def test_meta(self):

        class AlphaResource(ResourceView):
            pass
        self.assertEqual(AlphaResource._meta.name, 'alpha')

        class BetaResource(ResourceView):
            pass
        self.assertEqual(BetaResource._meta.name, 'beta')
        self.assertEqual(BetaResource._meta.url_name, 'beta')

        class GammaResource(ResourceView):

            class Meta:
                parent = BetaResource

        self.assertEqual(GammaResource._meta.parents, [BetaResource])
        self.assertEqual(GammaResource._meta.name, 'gamma')
        self.assertEqual(GammaResource._meta.url_name, 'beta-gamma')

    def test_resources(self):

        pirate = mixer.blend('core.pirate')
        for _ in xrange(3):
            mixer.blend('core.boat', pirate=pirate)

        self.assertEqual(pirate.boat_set.count(), 3)

        self.delete_resource('pirate-boat', pirate=pirate, data=dict(
            boat=[b.pk for b in pirate.boat_set.all()[:2]]
        ))
        self.assertEqual(pirate.boat_set.count(), 1)

    def test_urls(self):
        class AlphaResource(ResourceView):
            pass

        self.assertEqual(
            AlphaResource._meta.url_regex, 'alpha/(?P<alpha>[^/]+)?')

        class BetaResource(ResourceView):
            class Meta:
                parent = AlphaResource

        self.assertEqual(
            BetaResource._meta.url_regex,
            'alpha/(?P<alpha>[^/]+)?/beta/(?P<beta>[^/]+)?')

        class GammaResource(BetaResource):
            class Meta:
                prefix = 'gamma-prefix'

        self.assertEqual(
            GammaResource._meta.url_regex,
            'alpha/(?P<alpha>[^/]+)?/gamma-prefix/gamma/(?P<gamma>[^/]+)?')

        class ZetaResource(ResourceView):
            class Meta:
                parent = GammaResource

        self.assertEqual(
            ZetaResource._meta.url_regex,
            'alpha/(?P<alpha>[^/]+)?/gamma-prefix/gamma/(?P<gamma>[^/]+)?/zeta/(?P<zeta>[^/]+)?') # nolint

# lint_ignore=F0401,C0110
