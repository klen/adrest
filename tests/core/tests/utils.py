from django.test import TestCase
from adrest.utils import tools
from adrest.tests import AdrestRequestFactory


class UtilsTests(TestCase):

    def test_as_tuple(self):
        self.assertEqual(tools.as_tuple(None), tuple())
        self.assertEqual(tools.as_tuple(''), tuple())
        self.assertEqual(tools.as_tuple([]), tuple())
        self.assertEqual(tools.as_tuple([1, 2]), (1, 2))
        self.assertEqual(tools.as_tuple(set([1, 2])), (1, 2))
        self.assertEqual(tools.as_tuple({1: 1}), ({1: 1},))
        test = object()
        self.assertEqual(tools.as_tuple(test), (test,))

    def test_fix_request(self):
        rf = AdrestRequestFactory()
        request = rf.put('/test', {
            'foo': 'bar'
        })
        self.assertFalse(request.REQUEST.items())

        fixed = tools.fix_request(request)
        self.assertTrue(fixed.adrest_fixed)
        self.assertTrue(fixed.REQUEST.items())
