from django.http import QueryDict
from django.utils import simplejson

from ..utils.emitter import JSONPEmitter, JSONEmitter
from ..utils.parser import JSONParser, FormParser
from ..utils.exceptions import HttpError
from ..views import ResourceView
from ..utils.status import HTTP_409_CONFLICT
from ..utils.tools import as_tuple


class JSONRPCResource(ResourceView):
    """
        JSON RPC support.
        -----------------

        Implementation of remote procedure call encoded in JSON.
        Allows for notifications (info sent to the server that does not require a response)
        and for multiple calls to be sent to the server which may be answered out of order.

    """
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

            resource_name, method = method.split(self.separator, 1)

            data = QueryDict('', mutable=True)
            data.update(payload.get('data', dict()))
            data['callback'] = payload.get('callback') or request.GET.get('callback') or request.GET.get('jsonp') or 'callback'

            for h, v in payload.get('headers', dict()).iteritems():
                request.META["HTTP_%s" % h.upper().replace('-', '_')] = v

            request.POST = request.PUT = request.GET = data
            delattr(request, '_request')

            request.method = method.upper()

        except AssertionError, e:
            raise HttpError('Invalid RPC Call. %s' % e, status=HTTP_409_CONFLICT)

        except (ValueError, KeyError, TypeError):
            raise HttpError('Invalid RPC Payload.', status=HTTP_409_CONFLICT)

        params = payload.get('params', dict())
        response = self.api.call(resource_name, request, **params)
        response.finaly = True
        return response


class RPCResource(ResourceView):

    allowed_methods = 'get', 'post'
    url_regex = r'^rpc$'
    emitters = JSONEmitter, JSONPEmitter
    parsers = JSONParser, FormParser
    scheme = None

    def __init__(self, scheme=None, **kwargs):
        self.methods = dict()
        if scheme:
            self.scheme = scheme
        self.configure_rpc(self.scheme)
        super(RPCResource, self).__init__(**kwargs)

    def configure_rpc(self, scheme):
        if scheme is None:
            raise ValueError("Invalid RPC scheme.")

        for m in [getattr(scheme, m) for m in dir(scheme) if hasattr(getattr(scheme, m), '__call__')]:
            self.methods[m.__name__] = m

    def handle_request(self, request, **resources):
        payload = request.data

        try:

            if request.method == 'GET':
                payload = request.GET.get('payload')
                try:
                    payload = simplejson.loads(payload)
                except TypeError:
                    raise AssertionError("Invalid RPC Call.")

            assert 'method' in payload, "Invalid RPC Call."
            return self.rpc_call(request, **payload)

        except Exception, e:
            return dict(error=dict(message=str(e)))

    def rpc_call(self, request, method=None, params=None, **kwargs):
        args = []
        kwargs = dict()
        if isinstance(params, dict):
            kwargs.update(params)
        else:
            args = as_tuple(params)

        assert method in self.methods, "Unknown method: {0}".format(method)
        return self.methods[method](*args, **kwargs)


class AutoJSONRPC(RPCResource):
    separator = '.'

    def configure_rpc(self, scheme):
        pass

    def rpc_call(self, request, method=None, **payload):
        """ Call REST API with RPC force.
        """
        assert method and self.separator in method, "Wrong method name: {0}".format(method)

        resource_name, method = method.split(self.separator, 1)
        assert resource_name in self.api.resources, "Unknown method"

        data = QueryDict('', mutable=True)
        data.update(payload.get('data', dict()))
        data['callback'] = payload.get('callback') or request.GET.get('callback') or request.GET.get('jsonp') or 'callback'
        for h, v in payload.get('headers', dict()).iteritems():
            request.META["HTTP_%s" % h.upper().replace('-', '_')] = v

        request.POST = request.PUT = request.GET = data
        delattr(request, '_request')
        request.method = method.upper()
        request.META['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        params = payload.pop('params', dict())
        response = self.api.call(resource_name, request, **params)
        response.finaly = True
        assert response.status_code == 200, response.content
        return response


# pymode:lint_ignore=E1103,W0703
