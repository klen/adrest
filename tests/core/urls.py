from django.conf.urls.defaults import include, patterns

from ..main.api import API as main
from ..main.resources import DummyResource
from ..rpc.api import API as rpc
from ..simple.api import API as simple
from .api import api as pirates


urlpatterns = main.urls + patterns(
    '',
    DummyResource.as_url(),
    (r'^simple/', include(simple.urls)),
    (r'^rpc/', include(rpc.urls)),
    (r'^pirates/', include(pirates.urls)),
)
