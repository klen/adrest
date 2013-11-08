""" Collect URLS from apps. """
from django.conf.urls import include, patterns

from ..main.api import API as main
from ..main.resources import DummyResource
from ..rpc.api import API as rpc
from .api import api as pirates, api2 as pirates2


urlpatterns = main.urls + patterns(
    '',
    DummyResource.as_url(),
    (r'^rpc/', include(rpc.urls)),

    (r'^pirates/', include(pirates.urls)),
    (r'^pirates2/', include(pirates2.urls)),

)
