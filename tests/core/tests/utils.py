from django.test import TestCase


class UtilsTests(TestCase):

    def test_as_tuple(self):
        from adrest.utils.tools import as_tuple

        self.assertEqual(as_tuple(None), tuple())
        self.assertEqual(as_tuple(''), tuple())
        self.assertEqual(as_tuple([]), tuple())
        self.assertEqual(as_tuple([1, 2]), (1, 2))
        self.assertEqual(as_tuple(set([1, 2])), (1, 2))
        self.assertEqual(as_tuple({1: 1}), ({1: 1},))
        test = object()
        self.assertEqual(as_tuple(test), (test,))
