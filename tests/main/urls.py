from api import api
from simple.api import API


urlpatterns = api.urls + API.urls
