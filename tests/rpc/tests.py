from adrest.tests.utils import AdrestTestCase

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

    def test_base(self):
        uri = self.reverse('test')
        self.assertEqual(uri, '/rpc/test/')

        response = self.get_resource('test')
        self.assertContains(response, 'true')

    def test_rpc_resource(self):
        uri = self.reverse('rpc')
        self.assertEqual(uri, '/rpc/rpc')

        response = self.get_resource('rpc')
        self.assertContains(response, 'Payload', status_code=402)

        response = self.rpc(dict(
            method='blablabla'
        ))
        self.assertContains(response, 'Wrong method', status_code=402)

        response = self.rpc(dict(
            method='bla.bla'
        ))
        self.assertContains(response, 'Invalid', status_code=402)

        response = self.rpc(dict(
            method='test.bla'
        ))
        self.assertContains(response, 'Invalid', status_code=402)

    def test_rpc_get(self):
        response = self.rpc(dict(
            method='test.get'
        ))
        self.assertContains(response, 'true')

        response = self.rpc(dict(
            method='root.get',
            headers=dict(Authorization=111)
        ))
        self.assertContains(response, 'test_root')

        response = self.rpc(dict(
            method='root-child.get',
            params=dict(root=self.root1.pk)
        ))
        self.assertContains(response, '"count": 10')
        self.assertContains(response, 'test_child1')
        self.assertNotContains(response, 'test_child2')

        response = self.rpc(dict(
            method='root-child.get',
            params=dict(root=self.root2.pk),
            data=dict(odd=1)
        ))
        self.assertContains(response, '"count": 5')

    def test_rpc_post(self):
        response = self.rpc(dict(
            method='root.post',
            data=dict(name='root3')
        ), key=111)
        self.assertContains(response, 'root3')

        response = self.rpc(dict(
            method='root-child.post',
            params=dict(root=self.root1.pk),
            data=dict(name='child3')
        ), key=111)
        self.assertContains(response, 'child3')

        child = Child.objects.get(name='child3')
        self.assertEqual(child.root, self.root1)

        response = self.rpc(dict(
            method='root-child.post',
            params=dict(root=self.root1.pk),
            data=dict(name='child4', root=self.root2.pk)
        ), key=111)
        self.assertContains(response, 'child4')

        child = Child.objects.get(name='child4')
        self.assertEqual(child.root, self.root1)

    def test_rpc_put(self):
        response = self.rpc(dict(
            method='root-child.put',
            params=dict(root=self.root1.pk, child=self.root1.child_set.all()[0].pk),
            data=dict(name='New name')
        ))
        self.assertContains(response, 'New name')
        child = self.root1.child_set.all()[0]
        self.assertEqual(child.name, 'New name')

    def test_rpc_jsonp(self):
        response = self.rpc(dict(
            method='test.get',
        ), callback='test1234', headers=dict(HTTP_ACCEPT='text/javascript'))
        self.assertEqual(response.get('Content-type'), 'text/javascript')
        self.assertContains(response, 'test1234')

        response = self.rpc(dict(
            method='test.get',
        ), callback='jsonp', headers=dict(HTTP_ACCEPT='text/javascript'))
        self.assertContains(response, 'jsonp')

        response = self.rpc(dict(
            method='test.get',
            callback='parseJSON'
        ), headers=dict(HTTP_ACCEPT='text/javascript'))
        self.assertContains(response, 'parseJSON')

        response = self.rpc(dict(
            method='test.get',
            callback='parseJSON'
        ), callback='Other', headers=dict(HTTP_ACCEPT='text/javascript'))
        self.assertContains(response, 'parseJSON')

        response = self.rpc(dict(
            method='test.get',
            data=dict(error=True)
        ), headers=dict(HTTP_ACCEPT='text/javascript'))
        self.assertEqual(response.get('Content-type'), 'text/javascript')
        self.assertContains(response, 'callback("Custom error")', status_code=400)
