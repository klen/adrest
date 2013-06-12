from django.test import RequestFactory
from django.views.generic import View
from mixer.backend.django import mixer

from ..api import api as API
from adrest.mixin import DynamicMixin


class CoreDynamicTest(API.testCase):

    def test_base(self):

        pirates = mixer.cycle(3).blend('core.pirate')

        class SomeResource(DynamicMixin, View):

            class Meta:
                model = 'core.pirate'

            def dispatch(self, request, **resources):
                return self.get_collection(request, **resources)

        rf = RequestFactory()
        resource = SomeResource()

        response = resource.dispatch(rf.get('/'))
        self.assertEqual(len(response), len(pirates))

        response = resource.dispatch(rf.get('/?name=' + pirates[0].name))
        self.assertEqual(list(response), [pirates[0]])

        response = resource.dispatch(
            rf.get('/?adr-sort=name&adr-sort=captain'))
        self.assertEqual(list(response), sorted(
            pirates, key=lambda p: (p.name, p.captain)))

    def test_pagination(self):

        pirates = mixer.cycle(3).blend('core.pirate')

        class SomeResource(DynamicMixin, View):

            class Meta:
                model = 'core.pirate'
                limit_per_page = 2

            def dispatch(self, request, **resources):
                collection = self.get_collection(request, **resources)
                return self.paginate(request, collection)

        rf = RequestFactory()
        resource = SomeResource()

        response = resource.dispatch(rf.get('/'))
        self.assertEqual(len(response.resources), 2)

        resource._meta.limit_per_page = 0
        response = resource.dispatch(rf.get('/'))
        self.assertEqual(len(response), len(pirates))

        response = resource.dispatch(rf.get('/?adr-max=1'))
        self.assertEqual(len(response.resources), 1)

# lint_ignore=C0110,E1103
