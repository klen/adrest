from adrest.api import Api
from adrest.utils.auth import BaseAuthenticator
from adrest.utils.emitter import XMLEmitter
from adrest.views import ResourceView


class TestAuth(BaseAuthenticator):

    def authenticate(self, request=None):
        self.identifier = request.META.get('HTTP_AUTHORIZATION')
        return self.identifier


class TestResource(ResourceView):
    allowed_methods = 'GET', 'POST', 'PUT'
    model = 'rpc.test'

    def get(self, request, **resources):
        assert not 'error' in request.GET, "Custom error"
        return True


class RootResource(ResourceView):
    allowed_methods = 'GET', 'POST', 'PUT'
    model = 'rpc.root'


class ChildResource(ResourceView):
    allowed_methods = 'GET', 'POST', 'PUT'
    parent = RootResource
    model = 'rpc.child'


API = Api(api_rpc=True, emitters=(XMLEmitter,))
API.register(TestResource)
API.register(RootResource, authenticators=TestAuth)
API.register(ChildResource)
