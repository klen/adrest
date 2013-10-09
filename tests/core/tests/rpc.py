from ..api import api as API


class AutoJSONRPCTest(API.testCase):

    def test_base(self):
        self.assertTrue('autojsonrpc' in self.api.resources)

        uri = self.reverse('autojsonrpc')
        self.assertEqual(uri, '/pirates/rpc')

        response = self.get_resource('autojsonrpc')
        self.assertContains(response, 'Invalid RPC Call.')

# lint_ignore=C0110
