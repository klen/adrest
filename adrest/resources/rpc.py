from django.http import QueryDict, HttpResponse
from django.utils import simplejson, importlib

from ..utils.emitter import JSONPEmitter, JSONEmitter
from ..utils.parser import JSONParser, FormParser
from ..utils.tools import as_tuple
from ..utils.response import SerializedHttpResponse
from ..views import ResourceView, ResourceMetaClass


__all__ = 'get_request', 'RPCResource', 'AutoJSONRPC'


def get_request(func):
    """ Mark function as needed in request.
    """
    func.request = True
    return func


class RPCMeta(ResourceMetaClass):
    """ Setup RPC methods by Scheme.
    """
    def __new__(mcs, name, bases, params):
        cls = super(RPCMeta, mcs).__new__(mcs, name, bases, params)
        cls.configure_rpc()
        return cls


class RPCResource(ResourceView):
    """
        JSON RPC support.
        -----------------

        Implementation of remote procedure call encoded in JSON.
        Allows for notifications (info sent to the server that does not require
        a response) and for multiple calls to be sent to the server which may
        be answered out of order.

    """

    allowed_methods = 'get', 'post'
    emitters = JSONEmitter, JSONPEmitter
    methods = dict()
    parsers = JSONParser, FormParser
    scheme = None
    url_regex = r'^rpc$'

    __metaclass__ = RPCMeta

    def __init__(self, scheme=None, **kwargs):
        if scheme:
            self.configure_rpc(scheme)
        super(RPCResource, self).__init__(**kwargs)

    @classmethod
    def configure_rpc(cls, scheme=None):
        """ Get method from scheme.
        """
        scheme = scheme or cls.scheme
        if not cls.scheme:
            return False

        if isinstance(scheme, basestring):
            scheme = importlib.import_module(scheme)

        methods = getattr(scheme, '__all__', None) \
            or [m for m in dir(scheme) if not m.startswith('_')]

        for mname in methods:
            method = getattr(scheme, mname)
            if hasattr(method, '__call__'):
                cls.methods[method.__name__] = method

    def handle_request(self, request, **resources):

        if request.method == 'OPTIONS':
            return super(RPCResource, self).handle_request(
                request, **resources)

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
            return SerializedHttpResponse(
                dict(error=dict(message=str(e))),
                error=True
            )

    def rpc_call(self, request, method=None, params=None, **kwargs):
        args = []
        kwargs = dict()
        if isinstance(params, dict):
            kwargs.update(params)
        else:
            args = list(as_tuple(params))

        assert method in self.methods, "Unknown method: {0}".format(method)
        method = self.methods[method]
        if hasattr(method, 'request'):
            args.insert(0, request)

        return method(*args, **kwargs)


class AutoJSONRPC(RPCResource):
    """
        Automatic JSONRPC Api from REST
        -------------------------------

        Automatic Implementation of remote procedure call based on your REST.

    """
    separator = '.'
    url_name = 'autojsonrpc'

    @staticmethod
    def configure_rpc(scheme=None):
        pass

    def rpc_call(self, request, method=None, **payload):
        """ Call REST API with RPC force.
        """
        assert method and self.separator in method, \
            "Wrong method name: {0}".format(method)

        resource_name, method = method.split(self.separator, 1)
        assert resource_name in self.api.resources, "Unknown method"

        data = QueryDict('', mutable=True)
        data.update(payload.get('data', dict()))
        data['callback'] = payload.get('callback') or request.GET.get(
            'callback') or request.GET.get('jsonp') or 'callback'
        for h, v in payload.get('headers', dict()).iteritems():
            request.META["HTTP_%s" % h.upper().replace('-', '_')] = v

        request.POST = request.PUT = request.GET = data
        delattr(request, '_request')
        request.method = method.upper()
        request.META['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
        params = payload.pop('params', dict())
        response = self.api.call(resource_name, request, **params)

        # Make response for prevent serialization
        new_response = HttpResponse(response.content,
                                    status=response.status_code)
        new_response._headers = response._headers # nolint
        assert new_response.status_code == 200, new_response.content
        return new_response


# pymode:lint_ignore=E1103,W0703
