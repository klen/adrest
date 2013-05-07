from adrest.tests import AdrestTestCase
from ..api import api as API
from milkman.dairy import milkman


class CoreAdrestTests(AdrestTestCase):

    api = API

    def test_json(self):
        pirate = milkman.deliver('core.pirate', character='good')

        response = self.put_resource(
            'pirate', pirate=pirate, json=True, data=dict(name='John'))
        self.assertContains(response, '"name": "John"')

# lint_ignore=F0401
