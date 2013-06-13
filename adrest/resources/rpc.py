""" RPC support. """
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

    :return function: marked function.

    """
    func.request = True
    return func


class RPCMeta(ResourceMetaClass):

    """ Setup RPC methods by Scheme. """

    def __new__(mcs, name, bases, params):
        cls = super(RPCMeta, mcs).__new__(mcs, name, bases, params)
        cls.configure_rpc()
        return cls


class RPCResource(ResourceView):

    """ JSON RPC support.

    Implementation of remote procedure call encoded in JSON.
    Allows for notifications (info sent to the server that does not require
    a response) and for multiple calls to be sent to the server which may
    be answered out of order.

    """

    class Meta:
        allowed_methods = 'get', 'post'
        emitters = JSONEmitter, JSONPEmitter
        parsers = JSONParser, FormParser
        scheme = None
        url_regex = r'^rpc$'

    methods = dict()
    scheme_name = ''

    __metaclass__ = RPCMeta

    def __init__(self, scheme=None, **kwargs):
        if scheme:
            self.configure_rpc(scheme)
        super(RPCResource, self).__init__(**kwargs)

    @classmethod
    def configure_rpc(cls, scheme=None):
        """ Get methods from scheme. """
        scheme = scheme or cls._meta.scheme

        if not scheme:
            return

        if isinstance(scheme, basestring):
            scheme = importlib.import_module(scheme)

        cls.scheme_name = scheme.__name__

        methods = getattr(scheme, '__all__', None) \
            or [m for m in dir(scheme) if not m.startswith('_')]

        for mname in methods:
            method = getattr(scheme, mname)
            if hasattr(method, '__call__'):
                cls.methods["{0}.{1}".format(
                    cls.scheme_name, method.__name__)] = method

    def handle_request(self, request, **resources):
        """ Call RPC method.

        :return object: call's result

        """

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

            if 'method' not in payload:
                raise AssertionError("Invalid RPC Call.")
            return self.rpc_call(request, **payload)

        except Exception, e:
            return SerializedHttpResponse(
                dict(error=dict(message=str(e))),
                error=True
            )

    def rpc_call(self, request, method=None, params=None, **kwargs):
        """ Call a RPC method.

        return object: a result

        """
        args = []
        kwargs = dict()
        if isinstance(params, dict):
            kwargs.update(params)
        else:
            args = list(as_tuple(params))

        method_key = "{0}.{1}".format(self.scheme_name, method)
        if method_key not in self.methods:
            raise AssertionError("Unknown method: {0}".format(method))
        method = self.methods[method_key]

        if hasattr(method, 'request'):
            args.insert(0, request)

        return method(*args, **kwargs)


class AutoJSONRPC(RPCResource):

    """ Automatic JSONRPC Api from REST.

    Automatic Implementation of remote procedure call based on your REST.

    """

    separator = '.'

    class Meta:
        url_name = 'autojsonrpc'

    @staticmethod
    def configure_rpc(scheme=None):
        """ Do nothing. """
        pass

    def rpc_call(self, request, method=None, **payload):
        """ Call REST API with RPC force.

        return object: a result

        """
        if not method or self.separator not in method:
            raise AssertionError("Wrong method name: {0}".format(method))

        resource_name, method = method.split(self.separator, 1)
        if resource_name not in self.api.resources:
            raise AssertionError("Unknown method " + method)

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

        if not isinstance(response, SerializedHttpResponse):
            return response

        if response['Content-type'] in self._meta.emitters_dict:
            return HttpResponse(response.content, status=response.status_code)

        if response.status_code == 200:
            return response.response

        raise AssertionError(response.response)


# pymode:lint_ignore=E1103,W0703
