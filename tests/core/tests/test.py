from mixer.backend.django import mixer

from ..api import api as API
from adrest.tests import AdrestTestCase


class CoreAdrestTests(AdrestTestCase):

    api = API

    def test_json(self):
        pirate = mixer.blend('core.pirate', character='good')

        response = self.put_resource(
            'pirate', pirate=pirate, json=True, data=dict(name='John'))
        self.assertContains(response, '"name": "John"')

# lint_ignore=F0401,C
