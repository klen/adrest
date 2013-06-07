""" Test the integration with Django admin.
"""

from django.test import TestCase


class CoreAdminTest(TestCase):

    """ Check ADRest models in Django admin. """

    def test_admin(self):
        """ Checking for ADRest models are registered. """
        from django.contrib import admin
        admin.autodiscover()

        from adrest.models import AccessKey
        self.assertTrue(AccessKey in admin.site._registry)

        from adrest.models import Access
        self.assertTrue(Access in admin.site._registry)

# lint_ignore=W0212
