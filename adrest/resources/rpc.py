from django.http import QueryDict
from django.utils import simplejson

from ..utils.emitter import JSONPEmitter, JSONEmitter
from ..utils.exceptions import HttpError
from ..views import ResourceView
from ..utils.status import HTTP_409_CONFLICT


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

    def __init__(self, *args, **kwargs):
        self.target_resource = None
        super(JSONRPCResource, self).__init__(*args, **kwargs)

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

        self.target_resource = self.api.resources.get(resource_name)
        params = payload.get('params', dict())
        return self.api.call(resource_name, request, _emit_=False, **params)
        # resource = resource.as_view(api=self.api)
        # return resource(request, _emit_=False, **payload.get("params", dict()))

    def get_name(self):
        if self.target_resource:
            return self.target_resource.meta.name
        return self.meta.name


class AbstractRPC(object):

    @staticmethod
    def dispatch(request):

        try:
            payload = request.GET.get('payload') if request.method == 'GET' else request.raw_post_data

            if request.method == 'GET':
                payload = request.GET['payload']

            elif request.method == 'POST':
                payload = request.raw_post_data

            method = payload['method']
            params = payload.get('params', payload.get('data', dict()))

            assert all(payload, method), "Wrong payload."

        except (AssertionError, KeyError, ValueError), e:
            raise HttpError('Invalid RPC Call. %s' % e, status=HTTP_409_CONFLICT)



# pymode:lint_ignore=E1103
