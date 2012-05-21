from django.conf.urls.defaults import include, patterns

from simple.api import API as simple
from rpc.api import API as rpc
from .api import API as main


urlpatterns = main.urls + patterns('',
    (r'^simple/', include(simple.urls)),
    (r'^rpc/', include(rpc.urls)),
)
