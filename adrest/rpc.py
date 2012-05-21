from adrest.utils.exceptions import HttpError
from adrest.utils.status import HTTP_402_PAYMENT_REQUIRED
from django.utils import simplejson
from django.http import QueryDict

from .views import ResourceView


class RPCResource(ResourceView):
    " Auto generated RPC. "

    url_regex = r'^rpc$'

    SEPARATOR = '.'

    def get(self, request, **resources):
        try:
            payload = request.GET.get('payload')
            payload = simplejson.loads(payload)
            assert payload, "Payload not found."

            method = payload['method']
            assert method and self.SEPARATOR in method, "Wrong method name: %s." % method

            resource, method = method.split(self.SEPARATOR, 1)
            resource = self.api.resources.get(resource)
            assert resource and hasattr(resource, method), "Wrong resource: %s.%s" % (resource, method)

            data = QueryDict('', mutable=True)
            data.update(payload.get('data', dict()))
            request.POST = request.PUT = request.GET = data

        except AssertionError, e:
            raise HttpError('Invalid RPC Call. %s' % e, status=HTTP_402_PAYMENT_REQUIRED)

        except (ValueError, KeyError, TypeError):
            raise HttpError('Invalid RPC Payload.', status=HTTP_402_PAYMENT_REQUIRED)

        resource = resource.as_view(api=self.api)
        request.method = method.upper()
        return resource(request, **payload.get("params", dict()))

    def emit(self, response, **kwargs):
        return response
