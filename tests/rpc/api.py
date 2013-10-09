from adrest.api import Api
from adrest.utils.auth import AnonimousAuthenticator
from adrest.utils.emitter import XMLEmitter, JSONTemplateEmitter
from adrest.views import ResourceView
from adrest.resources.rpc import RPCResource, JSONEmitter, JSONPEmitter


API = Api('1.0.0', api_rpc=True, emitters=XMLEmitter)


class TestAuth(AnonimousAuthenticator):

    def authenticate(self, request):
        return request.META.get('HTTP_AUTHORIZATION')

    def configure(self, request):
        self.resource.identifier = request.META.get('HTTP_AUTHORIZATION')


class TestResource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'POST', 'PUT'
        model = 'rpc.test'

    def get(self, request, **resources):
        assert not 'error' in request.GET, "Custom error"
        return True


class RootResource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'POST', 'PUT'
        model = 'rpc.root'


@API.register
class ChildResource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'POST', 'PUT'
        parent = RootResource
        model = 'rpc.child'


class CustomResource(ResourceView):

    class Meta:
        model = 'rpc.custom'


API.register(ChildResource)
API.register(CustomResource, emitters=JSONTemplateEmitter)
API.register(RootResource, authenticators=TestAuth)
API.register(RPCResource, url_regex=r'^rpc2$', url_name='rpc2',
             scheme='tests.rpc.dummy', emitters=(JSONEmitter, JSONPEmitter))
API.register(TestResource)

# lint_ignore=C
