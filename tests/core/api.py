from adrest.views import ResourceView
from adrest.api import Api


class PirateResource(ResourceView):

    class Meta:
        allowed_methods = 'get', 'POST', 'pUt', 'delete', 'Patch'
        model = 'core.pirate'


class BoatResource(ResourceView):

    class Meta:
        allowed_methods = 'get', 'post', 'put', 'delete'
        model = 'core.boat'
        parent = PirateResource


api = Api()
api.register(PirateResource)
api.register(BoatResource)

# lint_ignore=C
