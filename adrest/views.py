import logging

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.base import ModelBase, Model
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from adrest import status, settings
from adrest.auth import AuthenticatorMixin, AnonimousAuthenticator
from adrest.emitters import EmitterMixin, JSONEmitter
from adrest.handlers import HandlerMixin
from adrest.parsers import ParserMixin
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
        self.models = []


class ResourceMetaClass(type):
    """ MetaClass for ResourceView.
        Create meta options.
    """

    def __new__(mcs, cls_name, bases, params):
        allowed_methods = params.get('allowed_methods')
        if allowed_methods:
            params['allowed_methods'] = as_tuple(allowed_methods)
        params['meta'] = meta = ResourceOptions()
        cls = super(ResourceMetaClass, mcs).__new__(mcs, cls_name, bases, params)
        if cls.parent:
            try:
                pmeta = getattr(cls.parent, 'meta')
                meta.parents = pmeta.parents + [cls.parent]
            except AttributeError:
                raise TypeError("%s.parent must be instance of %s" % (cls_name, "ResourceView"))

        if cls.model:
            if not isinstance(cls.model, (ModelBase, Model)):
                raise TypeError("%s.model must be instance of Model" % cls_name)
            meta.name = cls.model._meta.module_name
        else:
            name_bits = [bit for bit in cls_name.split('Resource') if bit]
            meta.name = ''.join(name_bits).lower()

        uri_params = cls.uri_params or []
        meta.urlname = '-'.join(([ cls.parent.meta.urlname ] if cls.parent else []) +
                ([ cls.prefix ] if cls.prefix else []) +
                list(uri_params) +
                [ meta.name ])
        meta.urlregex = '/'.join(
                '%(name)s/(?P<%(name)s>[^/]+)' % dict(name = p)
                for p in (
                    [p.meta.name for p in meta.parents] + list(uri_params)))
        meta.urlregex = meta.urlregex + '/' if meta.urlregex else ''
        if cls.prefix:
            meta.urlregex = '%s%s/' % (meta.urlregex, cls.prefix)
        meta.urlregex += '%(name)s/(?:(?P<%(name)s>[^/]+)/)?$' % dict(
                name = meta.name)

        meta.models = [o.model for o in meta.parents + [ cls ] if o.model]
        return cls


class ResourceView(HandlerMixin, ThrottleMixin, EmitterMixin, ParserMixin,
        AuthenticatorMixin, View):

    # Create meta options
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
            if method == 'OPTIONS' and not settings.AUTHENTICATE_OPTIONS_REQUEST:
                self.identifier = 'anonymous'
            else:
                self.identifier = self.authenticate()

            # Throttle check
            self.throttle_check()

            # Get required resources
            resources = self.get_resources_from_uri(**kwargs)

            # Check rights
            self.check_rights(resources, method)

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

    def get_resources_from_uri(self, **resources):
        """ Parse form params from URI.
        """
        mdict = dict((m._meta.module_name, m) for m in self.meta.models)

        # URL objects
        for key, value in resources.iteritems():
            key = key.lower()
            if mdict.has_key(key) and value:
                try:
                    resources[key] = mdict.get(key).objects.get(pk=value)

                except (ObjectDoesNotExist, ValueError):
                    raise HttpError("Resource not found.", status=status.HTTP_404_NOT_FOUND)

                except MultipleObjectsReturned:
                    raise HttpError("Resources conflict.", status=status.HTTP_409_CONFLICT)

        # Check owners
        it = (m._meta.module_name for m in self.meta.models)
        try:
            f_name, c_name = next(it), next(it)

            while True:
                ofm, ocm = resources.get(f_name), resources.get(c_name)

                # Test parent element linked from children
                assert not ocm or getattr(ocm, '%s_id' % f_name, None) == ofm.pk

                f_name, c_name = c_name, next(it)

        except (AssertionError, ObjectDoesNotExist):
            raise HttpError("Access forbiden.", status=status.HTTP_403_FORBIDDEN)

        except StopIteration:
            pass

        instance = resources.get(self.meta.name)
        if instance:
            resources['instance'] = instance
        return resources

    @staticmethod
    def handle_exception(e):
        """ Handle code exception.
        """
        if settings.DEBUG:
            raise

        else:
            LOG.error(str(e))
            return Response(str(e), status=500)

    @property
    def version(self):
        return str(self.api or '')


class ApiMapResource(ResourceView):
    """ Simple JSON Api Map.
    """
    log = False
    emitters = JSONEmitter
    authenticators = AnonimousAuthenticator

    def get(self, *args, **Kwargs):
        resources = set()
        api_map = dict()
        for key in sorted( self.api._map.keys() ):
            rinfo = self.api._map[key]
            r = rinfo['resource']
            if r.meta.urlname in resources:
                continue
            resources.add(rinfo['urlname'])

            api_map[rinfo['urlregex']] = dict(
                name = rinfo['urlname'],
                methods = r.allowed_methods,
                model = r.model.__name__ if r.model else r.model,
            )
        return api_map
