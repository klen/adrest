from adrest.api import Api
from adrest.utils.auth import AnonimousAuthenticator
from adrest.utils.emitter import XMLEmitter
from adrest.views import ResourceView


class TestAuth(AnonimousAuthenticator):

    def authenticate(self, request):
        return request.META.get('HTTP_AUTHORIZATION')

    def configure(self, request):
        self.resource.identifier = request.META.get('HTTP_AUTHORIZATION')


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
