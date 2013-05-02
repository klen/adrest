from adrest.views import ResourceView
from adrest.api import Api


class PirateResource(ResourceView):
    allowed_methods = 'get', 'POST', 'pUt', 'delete', 'Patch'
    model = 'core.pirate'


class BoatResource(ResourceView):
    allowed_methods = 'get', 'post', 'put', 'delete'
    model = 'core.boat'
    parent = PirateResource


api = Api()
api.register(PirateResource)
api.register(BoatResource)
