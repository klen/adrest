""" Simple API for tests. """
from adrest.views import ResourceView
from adrest.api import Api


api = Api()


class PirateResource(ResourceView):

    """ Part of simple API for tests. """

    class Meta:
        allowed_methods = 'get', 'POST', 'pUt', 'delete', 'Patch'
        model = 'core.pirate'


@api.register
class BoatResource(ResourceView):

    """ Part of simple API for tests. """

    class Meta:
        allowed_methods = 'get', 'post', 'put', 'delete'
        model = 'core.boat'
        parent = PirateResource


api.register(PirateResource)
