from adrest.api import Api
from adrest.resources.rpc import RPCResource

from . import rpc
from .resources import * # nolint


api = Api(version='0.1')

api.register(AuthorResource)
api.register(BookResource)
api.register(RPCResource, scheme=rpc)
