""" Create Api and resources. """
from adrest.api import Api
from adrest.views import ResourceView
from adrest.resources.rpc import RPCResource

from . import rpc


api = Api(version='0.1')
api.register(RPCResource, scheme=rpc)


@api.register
class AuthorResource(ResourceView):

    """ Get authors from db. """

    class Meta:
        model = 'main.author'


@api.register
class BookResource(ResourceView):

    """ Works with books. Nested resource. """

    class Meta:
        allowed_methods = 'get', 'post', 'put'
        model = 'main.book'
        parent = AuthorResource
