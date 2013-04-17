from django.conf.urls.defaults import include, patterns
from ..rpc.api import API as rpc
from ..simple.api import API as simple
from ..main.api import API as main
from ..main.resources import DummyResource


urlpatterns = main.urls + patterns(
    '',
    DummyResource.as_url(),
    (r'^simple/', include(simple.urls)),
    (r'^rpc/', include(rpc.urls)),
)
