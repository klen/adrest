from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from adrest import status
from adrest.auth import AuthenticatorMixin
from adrest.emitters import EmitterMixin, XMLTemplateEmitter, JSONTemplateEmitter
from adrest.parsers import ParserMixin, XMLParser, JSONParser, FormParser
from adrest.utils import HttpError, Response


class ResourceView(EmitterMixin, ParserMixin, AuthenticatorMixin, View):

    api = None

    handler = None

    emitters = (XMLTemplateEmitter, JSONTemplateEmitter)

    parsers = (FormParser, XMLParser, JSONParser)

    callmap = { 'GET': 'get', 'POST': 'post',
                'PUT': 'put', 'DELETE': 'delete' }

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):

        self.request = request
        method = request.method.upper()

        try:
            # Check request method
            self.check_method_allowed(method)

            # Get the appropriate create/read/update/delete function
            func = getattr(self.handler, self.callmap.get(method, None))

            # Get required resources
            kwargs = self.parse_kwargs(self.handler, **kwargs)

            content_type = self.determine_content(request)
            # Parse content
            if method in ('POST', 'PUT') and content_type:
                request.data = self.parse(content_type)

            # Get function data
            content = func(request, *args, **kwargs)
            response = Response(content)

        except HttpError, e:
            response = Response(e.message, status=e.status)

        # Always add these headers
        response.headers['Allow'] = ', '.join(self.handler.allowed_methods)
        response.headers['Vary'] = 'Authenticate, Accept'

        return self.emit(response)

    def check_method_allowed(self, method):
        """ Ensure the request method is permitted for this resource, raising a ResourceException if it is not.
        """
        if not method in self.callmap.keys():
            raise HttpError('Unknown or unsupported method \'%s\'' % method, status=status.HTTP_501_NOT_IMPLEMENTED)

        if not method in self.handler.allowed_methods:
            raise HttpError('Method \'%s\' not allowed on this resource.' % method, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @property
    def version(self):
        return self.api.str_version if self.api else ''

    def determine_content(self, request):
        if not request.META.get('CONTENT_LENGTH', None) and not request.META.get('TRANSFER_ENCODING', None):
            return None
        return self.request.META.get('CONTENT_TYPE', None)

    @staticmethod
    def parse_kwargs(handler, **kwargs):
        models = dict()
        owners = dict()
        h = handler
        while h:
            if h.model:
                models[h.model._meta.module_name] = h.model
            h = h.parent

        for key, value in kwargs.iteritems():
            key = key.lower()
            if models.has_key(key) and value:
                try:
                    owners[key] = models.get(key).objects.get(pk=value)

                except ObjectDoesNotExist:
                    raise HttpError("Resource not found.", status=status.HTTP_404_NOT_FOUND)

                except MultipleObjectsReturned:
                    raise HttpError("Resources conflict.", status=status.HTTP_409_CONFLICT)

        kwargs.update(owners)
        kwargs['instance'] = kwargs.get(handler.resource_name)
        return kwargs
