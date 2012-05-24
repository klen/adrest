from django.http import QueryDict
from django.utils import simplejson

from .utils.emitter import JSONPEmitter, JSONEmitter
from .utils.exceptions import HttpError
from .utils.status import HTTP_402_PAYMENT_REQUIRED
from .views import ResourceView


class RPCResource(ResourceView):
    " Auto generated RPC. "

    url_regex = r'^rpc$'
    emitters = JSONEmitter, JSONPEmitter
    separator = '.'

    def get(self, request, **resources):
        try:
            payload = request.GET.get('payload')
            payload = simplejson.loads(payload)
            assert payload, "Payload not found."

            method = payload['method']
            assert method and self.separator in method, "Wrong method name: %s." % method

            resource, method = method.split(self.separator, 1)
            resource = self.api.resources.get(resource)
            assert resource and hasattr(resource, method), "Wrong resource: %s.%s" % (resource, method)

            data = QueryDict('', mutable=True)
            data.update(payload.get('data', dict()))
            data['callback'] = payload.get('callback') or request.GET.get('callback') or request.GET.get('jsonp') or 'callback'

            for h, v in payload.get('headers', dict()).iteritems():
                request.META["HTTP_%s" % h.upper().replace('-', '_')] = v

            request.POST = request.PUT = request.GET = data
            delattr(request, '_request')

        except AssertionError, e:
            raise HttpError('Invalid RPC Call. %s' % e, status=HTTP_402_PAYMENT_REQUIRED)

        except (ValueError, KeyError, TypeError):
            raise HttpError('Invalid RPC Payload.', status=HTTP_402_PAYMENT_REQUIRED)

        resource = resource.as_view(api=self.api)
        request.method = method.upper()
        return resource(request, **payload.get("params", dict()))
