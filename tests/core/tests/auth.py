""" Tests ADRest auth mixin.
"""
from django.views.generic import View

from ..api import api as API
from adrest.mixin import AuthMixin
from adrest.tests import AdrestTestCase
from adrest.utils.auth import UserAuthenticator


class CoreAuthTest(AdrestTestCase):

    """ Auth related tests. """

    api = API

    def test_meta(self):
        """ Test a meta attribute generation. """

        class Resource(View, AuthMixin):

            class Meta:
                model = 'core.pirate'
                authenticators = UserAuthenticator

        self.assertTrue(Resource._meta)
        self.assertTrue(Resource._meta.authenticators)
        self.assertEqual(Resource._meta.authenticators, (UserAuthenticator,))

# lint_ignore=W0212
