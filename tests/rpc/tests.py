from adrest.tests.utils import AdrestTestCase
from milkman.dairy import milkman
from django.utils import simplejson

from .api import API
from .models import Root, Child


class RPCTestCase(AdrestTestCase):
    api = API

    def setUp(self):
        self.root1 = Root.objects.create(name='test_root1')
        for i in xrange(10):
            Child.objects.create(root=self.root1, name='test_child1')

        self.root2 = Root.objects.create(name='test_root2')
        for i in xrange(10):
            Child.objects.create(root=self.root2, name='test_child2', odd=i % 2)

    def test_base_rpc(self):

        # POST args
        response = self.rpc(
            'rpc2',
            rpc=dict(
                jsonrpc='2.0',
                method='method1',
                params=['test'],
            ))
        self.assertEqual(response.content, '"Hello test"')

        # POST kwargs
        response = self.rpc(
            'rpc2',
            rpc=dict(
                jsonrpc='2.0',
                method='method2',
                params=dict(
                    start=200,
                    end=300
                )
            ))
        response = simplejson.loads(response.content)
        self.assertTrue(200 <= response <= 300)

        response = self.rpc(
            'rpc2',
            rpc=dict(
                jsonrpc='2.0',
                method='wrongmethodname',
            ))
        self.assertContains(response, "Unknown method")

        # Handle Errors
        response = self.rpc(
            'rpc2',
            rpc=dict(
                jsonrpc='2.0',
                method='error_method',
            ))
        response = simplejson.loads(response.content)
        self.assertEqual(response['error']['message'], 'Error here')

        # GET JSONRPC
        response = self.rpc(
            'rpc2',
            callback='answer',
            rpc=dict(
                jsonrpc='2.0',
                method='method1',
                params=['test'],
            ))
        self.assertEqual(response.content, 'answer("Hello test")')

    def test_base(self):
        uri = self.reverse('test')
        self.assertEqual(uri, '/rpc/test/')

        response = self.get_resource('test')
        self.assertContains(response, 'true')

    def test_autojsonrpc(self):
        uri = self.reverse('autojsonrpc')
        self.assertEqual(uri, '/rpc/rpc')

        response = self.get_resource('autojsonrpc')
        self.assertContains(response, 'Invalid RPC Call.')

        response = self.rpc(
            'autojsonrpc',
            callback='answer',
            rpc=dict(
                method="iamwrongmethod",
            )
        )
        self.assertContains(response, 'Wrong method')

        response = self.rpc(
            'autojsonrpc',
            callback='answer',
            rpc=dict(method='bla.bla'))
        self.assertContains(response, 'Unknown method')

        response = self.rpc(
            'autojsonrpc',
            rpc=dict(
            method='test.bla'))
        self.assertContains(response, 'unsupported method')

        response = self.rpc(
            'autojsonrpc',
            rpc=dict(
            method='test.get'))
        self.assertContains(response, 'true')

        response = self.rpc(
            'autojsonrpc',
            rpc=dict(
            method='root.get'))
        self.assertContains(response, 'Authorization required')

        response = self.rpc(
            'autojsonrpc',
            rpc=dict(
                headers=dict(Authorization=111),
                method='root.get'))
        self.assertContains(response, 'test_root')

        response = self.rpc(
            'autojsonrpc',
            rpc=dict(
                params=dict(root=self.root1.pk),
                method='root-child.get'))
        self.assertContains(response, '"count": 10')
        self.assertContains(response, 'test_child1')
        self.assertNotContains(response, 'test_child2')

        response = self.rpc(
            'autojsonrpc',
            rpc=dict(
                params=dict(root=self.root2.pk),
                data=dict(odd=1),
                method='root-child.get'))
        self.assertContains(response, '"count": 5')

        response = self.rpc(
            'autojsonrpc',
            key=111,
            rpc=dict(
                data=dict(name='root3'),
                method='root.post'))
        self.assertContains(response, 'root3')

        response = self.rpc(
            'autojsonrpc',
            key=111,
            rpc=dict(
                data=dict(name='child3'),
                params=dict(root=self.root1.pk),
                method='root-child.post'))
        self.assertContains(response, 'child3')

        child = Child.objects.get(name='child3')
        self.assertEqual(child.root, self.root1)

        response = self.rpc(
            'autojsonrpc',
            key=111,
            rpc=dict(
                data=dict(name='child4', root=self.root2.pk),
                params=dict(root=self.root1.pk),
                method='root-child.post'))
        self.assertContains(response, 'child4')

        child = Child.objects.get(name='child4')
        self.assertEqual(child.root, self.root1)

        response = self.rpc(
            'autojsonrpc',
            key=111,
            rpc=dict(
                data=dict(name='New name'),
                params=dict(root=self.root1.pk, child=self.root1.child_set.all()[0].pk),
                method='root-child.put'))
        self.assertContains(response, 'New name')
        child = self.root1.child_set.all()[0]
        self.assertEqual(child.name, 'New name')

        response = self.rpc(
            'autojsonrpc',
            callback='test1234',
            rpc=dict(method='test.get'))
        self.assertContains(response, 'test1234')

        response = self.rpc(
            'autojsonrpc',
            callback='test',
            rpc=dict(
                method='test.get',
                callback='test1234'))
        self.assertContains(response, 'test1234')

    def test_custom(self):
        milkman.deliver('rpc.custom')
        response = self.rpc(
            'autojsonrpc',
            rpc=dict(method='custom.get'))
        self.assertContains(response, 'Custom template')
