""" Tests ADRest emitter mixin.
"""
from django.views.generic import View

from ..api import api as API
from adrest.mixin import EmitterMixin
from adrest.tests import AdrestTestCase


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

# lint_ignore=W0212
