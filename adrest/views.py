from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from adrest import status
from adrest.auth import AuthenticatorMixin
from adrest.emitters import EmitterMixin, XMLTemplateEmitter, JSONTemplateEmitter
from adrest.handlers import HandlerMixin
from adrest.parsers import ParserMixin, XMLParser, JSONParser, FormParser
from adrest.signals import api_request_started, api_request_finished
from adrest.utils import HttpError, Response, as_tuple


class ResourceView(HandlerMixin, EmitterMixin, ParserMixin, AuthenticatorMixin, View):

    api = None

    log = True

    allowed_methods = ('GET', )

    emitters = (XMLTemplateEmitter, JSONTemplateEmitter)

    parsers = (FormParser, XMLParser, JSONParser)

    callmap = { 'GET': 'get', 'POST': 'post',
                'PUT': 'put', 'DELETE': 'delete' }

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):

        self.request = request

        # Send started signal
        api_request_started.send(self, request = request)

        method = request.method.upper()

        try:

            # Check request method
            self.check_method_allowed(method)

            # Authentificate
            self.identifier = self.authenticate()

            # Get the appropriate create/read/update/delete function
            func = getattr(self, self.callmap.get(method, None))

            # Get required resources
            resources = self.parse_resources(**kwargs)

            # Parse content
            if method in ('POST', 'PUT'):
                request.data = self.parse()

            # Get function data
            content = func(request, *args, **resources)
            response = Response(content)

        except HttpError, e:
            response = Response(e.message, status=e.status)

        except Exception, e:
            response = self.handle_exception(e)

        # Always add these headers
        response.headers['Allow'] = ', '.join(as_tuple(self.allowed_methods))
        response.headers['Vary'] = 'Authenticate, Accept'

        response = self.emit(response)

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

    @classmethod
    def get_resource_name(cls):
        if cls.model:
            return cls.model._meta.module_name
        class_name = cls.__name__
        name_bits = [bit for bit in class_name.split('Resource') if bit]
        return ''.join(name_bits).lower()

    @classmethod
    def get_urlname(cls):
        parts = []

        if cls.parent:
            parts.append(cls.parent.get_urlname())

        if cls.prefix:
            parts.append(cls.prefix)

        if cls.uri_params:
            parts += list(cls.uri_params)

        parts.append(cls.get_resource_name())
        return '-'.join(parts)

    @classmethod
    def get_urlregex(cls):
        parts = [p.get_resource_name() for p in cls.get_parents()]

        if cls.uri_params:
            parts += list(cls.uri_params)

        regex = '/'.join('%(name)s/(?P<%(name)s>[^/]+)' % dict(name = p) for p in parts)
        regex = regex + '/' if regex else ''
        regex += '%(name)s/(?:(?P<%(name)s>[^/]+)/)?$' % dict(name = cls.get_resource_name())
        if cls.prefix:
            regex = '%s/%s' % (cls.prefix, regex)
        return regex

    @classmethod
    def get_parents(cls):
        parents = list()
        while cls.parent:
            parents.append(cls.parent)
            cls = cls.parent
        return reversed(parents)

    @property
    def version(self):
        return self.api.str_version if self.api else ''

    def parse_resources(self, **kwargs):
        models = [p.model for p in self.get_parents() if p.model]
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
                assert getattr(ocm, '%s_id' % f_name, ofm.pk)
                f_name, c_name = c_name, next(it)

        except (AssertionError, ObjectDoesNotExist):
            raise HttpError("Access forbiden.", status=status.HTTP_403_FORBIDDEN)

        except StopIteration:
            pass

        for model in reversed(models):
            if owners.get(model._meta.module_name):
                pass

        kwargs['instance'] = kwargs.get(self.get_resource_name())
        return kwargs

    def handle_exception(self, e):
        return Response(str(e), status=500)
