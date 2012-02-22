from simple.api import API as simple

from .api import API as main


urlpatterns = main.urls + simple.urls
