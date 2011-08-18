import logging

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.base import ModelBase
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from adrest import status
from adrest.auth import AuthenticatorMixin, AnonimousAuthenticator
from adrest.emitters import EmitterMixin, JSONEmitter
from adrest.handlers import HandlerMixin
from adrest.parsers import ParserMixin
from adrest.settings import DEBUG, AUTHENTICATE_OPTIONS_REQUEST
from adrest.signals import api_request_started, api_request_finished
from adrest.throttle import ThrottleMixin
from adrest.utils import HttpError, Response, as_tuple


LOG = logging.getLogger('adrest')


class ResourceOptions(object):
    """ Resource meta options.
    """
    def __init__(self):
        self.name = self.urlname = self.urlregex = ''
        self.parents = []


class ResourceMetaClass(type):
    """ MetaClass for ResourceView.
        Create meta options.
    """

    def __new__(mcs, cls, bases, params):
        params['_meta'] = mcs.get_meta(cls, **params)
        allowed_methods = params.get('allowed_methods')
        if allowed_methods:
            params['allowed_methods'] = as_tuple(allowed_methods)
        return super(ResourceMetaClass, mcs).__new__(mcs, cls, bases, params)

    @staticmethod
    def get_meta(cls_name, parent=None, model=None, form=None, api=None,
            uri_params=None, prefix=None, **kwargs):
        rname = "ResourceView"
        meta = ResourceOptions()
        if parent:
            try:
                pmeta = getattr(parent, '_meta')
                meta.parents = pmeta.parents + [parent]
            except AttributeError:
                raise TypeError("%s.parent must be instance of %s" % (cls_name,
                    rname))

        if model:
            if not isinstance(model, ModelBase):
                raise TypeError(
                        "%s.model must be instance of Model" % cls_name)
            meta.name = model._meta.module_name
        else:
            name_bits = [bit for bit in cls_name.split('Resource') if bit]
            meta.name = ''.join(name_bits).lower()

        uri_params = uri_params or []
        meta.urlname = '-'.join(([ parent._meta.urlname ] if parent else []) +
                ([ prefix ] if prefix else []) +
                list(uri_params) +
                [ meta.name ])
        meta.urlregex = '/'.join(
                '%(name)s/(?P<%(name)s>[^/]+)' % dict(name = p)
                for p in (
                    [p._meta.name for p in meta.parents] + list(uri_params)))
        meta.urlregex = meta.urlregex + '/' if meta.urlregex else ''
        if prefix:
            meta.urlregex = '%s%s/' % (meta.urlregex, prefix)
        meta.urlregex += '%(name)s/(?:(?P<%(name)s>[^/]+)/)?$' % dict(
                name = meta.name)
        return meta


class ResourceView(HandlerMixin, ThrottleMixin, EmitterMixin, ParserMixin,
        AuthenticatorMixin, View):

    # Create _meta options
    __metaclass__ = ResourceMetaClass

    api = None
    log = True

    # Since we handle cross-origin XML HTTP requests, let OPTIONS be another
    # default allowed method.
    allowed_methods = 'GET', 'OPTIONS'

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):

        # Save request for later use
        self.request = request

        # Send started signal
        api_request_started.send(self, request = request)

        # Current HTTP method
        method = request.method.upper()

        try:

            # Check request method
            self.check_method_allowed(method)

            # Authentificate
            # We do not restrict access for OPTIONS request.
            if method == 'OPTIONS' and not AUTHENTICATE_OPTIONS_REQUEST:
                self.identifier = 'anonymous'
            else:
                self.identifier = self.authenticate()

            # Throttle check
            self.throttle_check()

            # Get required resources
            resources = self.parse_resources(**kwargs)

            # Parse content
            if method in ('POST', 'PUT'):
                request.data = self.parse()
                if isinstance(request.data, basestring):
                    request.data = dict()

            # Get the appropriate create/read/update/delete function
            func = getattr(self, self.callmap.get(method, None))

            # Get function data
            content = func(request, *args, **resources)
            response = Response(content)

        except HttpError, e:
            response = Response(e.message, status=e.status)

        except Exception, e:
            response = self.handle_exception(e)

        # Always add these headers
        response.headers['Allow'] = ', '.join(self.allowed_methods)
        response.headers['Vary'] = 'Authenticate, Accept'

        # Serialize response
        emitter = JSONEmitter if method == 'OPTIONS' else None
        response = self.emit(request, response, emitter=emitter)

        # Send finished signal
        api_request_finished.send(self, request=self.request, response=response)

        return response

    def check_method_allowed(self, method):
        """ Ensure the request method is permitted for this resource, raising a ResourceException if it is not.
        """
        if not method in self.callmap.keys():
            raise HttpError('Unknown or unsupported method \'%s\'' % method, status=status.HTTP_501_NOT_IMPLEMENTED)

        if not method in self.allowed_methods:
            raise HttpError('Method \'%s\' not allowed on this resource.' % method, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def parse_resources(self, **kwargs):
        models = [p.model for p in self._meta.parents if p.model]
        if self.model:
            models.append(self.model)
        models_dict = dict((m._meta.module_name, m) for m in models if m)
        owners = dict()

        for key, value in kwargs.iteritems():
            key = key.lower()
            if models_dict.has_key(key) and value:
                try:
                    owners[key] = models_dict.get(key).objects.get(pk=value)

                except (ObjectDoesNotExist, ValueError):
                    raise HttpError("Resource not found.", status=status.HTTP_404_NOT_FOUND)

                except MultipleObjectsReturned:
                    raise HttpError("Resources conflict.", status=status.HTTP_409_CONFLICT)

        kwargs.update(owners)

        # Check owners
        it = (m._meta.module_name for m in models)
        try:
            f_name = next(it)

            if self.auth:
                self.auth.test_owner(owners.get(f_name))

            c_name = next(it)

            while True:
                ofm, ocm = owners.get(f_name), owners.get(c_name)

                # Test parent element linked from children
                assert not ocm or getattr(ocm, '%s_id' % f_name, None) == ofm.pk

                f_name, c_name = c_name, next(it)

        except (AssertionError, ObjectDoesNotExist):
            raise HttpError("Access forbiden.", status=status.HTTP_403_FORBIDDEN)

        except StopIteration:
            pass

        for model in reversed(models):
            if owners.get(model._meta.module_name):
                pass

        kwargs['instance'] = kwargs.get(self._meta.name)
        return kwargs

    @staticmethod
    def handle_exception(e):
        """ Handle code exception.
        """
        if DEBUG:
            raise

        else:
            LOG.error(str(e))
            return Response(str(e), status=500)

    @property
    def version(self):
        return str(self.api or '')


class TopResource(ResourceView):
    """ TODO: Not implemented.
    """
    log = False
    emitters = JSONEmitter
    authenticators = AnonimousAuthenticator

    def dispatch(self, request, *args, **kwargs):
        return super(TopResource, self).dispatch(request, *args, **kwargs)
