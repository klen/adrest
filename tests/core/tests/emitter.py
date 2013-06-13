""" Tests ADRest emitter mixin.
"""
from django.views.generic import View

from ..api import api as API
from adrest.mixin import EmitterMixin
from adrest.tests import AdrestTestCase
from mixer.backend.django import mixer


class CoreEmitterTest(AdrestTestCase):

    """ Emitter related tests. """

    api = API

    def test_meta(self):
        """ Test a meta attribute generation. """

        class Resource(View, EmitterMixin):

            class Meta:
                model = 'core.pirate'

        self.assertTrue(Resource._meta)
        self.assertTrue(Resource._meta.emitters)

    def test_to_simple(self):
        """ Test resource's to simple method.

        :return :

        """

        pirates = mixer.cycle(2).blend('core.pirate')

        class Resource(View, EmitterMixin):

            class Meta:
                model = 'core.pirate'

            def to_simple(self, content, simple, serializer=None):

                return simple + ['HeyHey!']

        resource = Resource()
        response = resource.emit(pirates)
        self.assertTrue('HeyHey!' in response.content)

        class Resource(View, EmitterMixin):

            class Meta:
                model = 'core.pirate'

            @staticmethod
            def to_simple__name(pirate, serializer=None):

                return 'Evil ' + pirate.name

        resource = Resource()
        pirate = pirates[0]
        response = resource.emit(pirate)
        self.assertTrue('Evil ' + pirate.name in response.content)

    def test_model_options(self):

        boats = mixer.cycle(2).blend('core.boat')

        class Resource(View, EmitterMixin):

            class Meta:
                model = 'core.boat'
                emit_models = dict(
                    include='hooray'
                )

            @staticmethod
            def to_simple__hooray(boat, serializer=None):
                return 'hooray'

        resource = Resource()
        response = resource.emit(boats)
        self.assertTrue('hooray' in response.content)

        boat = boats[0]
        resource._meta.emit_models['exclude'] = 'title'
        response = resource.emit(boat)
        self.assertFalse(boat.title in response.content)

        resource._meta.emit_models['related'] = dict(
            pirate=dict(
                fields='name'
            )
        )
        response = resource.emit(boat)
        self.assertTrue(boat.pirate.name in response.content)

        class Resource(View, EmitterMixin):

            class Meta:
                model = 'core.boat'
                emit_include = 'hooray'

            @staticmethod
            def to_simple__hooray(boat, serializer=None):
                return 'hooray'

        resource = Resource()
        response = resource.emit(boats)
        self.assertTrue('hooray' in response.content)

    def test_format(self):
        pirate = mixer.blend('core.pirate')

        class Resource(View, EmitterMixin):
            class Meta:
                model = 'core.pirate'

        resource = Resource()
        response = resource.emit(pirate)
        self.assertTrue('fields' in response.content)

        resource._meta.emit_format = 'simple'
        response = resource.emit(pirate)
        self.assertFalse('fields' in response.content)


# lint_ignore=W0212,E0102,C0110
