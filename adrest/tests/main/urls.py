from api import api
from adrest.tests.simple.api import API


urlpatterns = api.urls + API.urls
