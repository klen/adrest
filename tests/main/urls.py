from django.conf.urls.defaults import include, patterns
from rpc.api import API as rpc
from simple.api import API as simple

from .api import API as main
from .resources import DummyResource


urlpatterns = main.urls + patterns('',
    DummyResource.as_url(),
    (r'^simple/', include(simple.urls)),
    (r'^rpc/', include(rpc.urls)),
)
