""" Base request resource. """

from logging import getLogger

from django.conf.urls.defaults import url
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .mixin import auth, emitter, handler, parser, throttle
from .settings import ADREST_CONFIG
from .signals import api_request_started, api_request_finished
from .utils import status
from .utils.exceptions import HttpError, FormError
from .utils.response import SerializedHttpResponse
from .utils.tools import as_tuple, gen_url_name, gen_url_regex, fix_request, import_functions

logger = getLogger('django.request')

__all__ = 'ResourceView',


NOTIFIERS = import_functions(ADREST_CONFIG['NOTIFIERS'])
LOG_HANDLERS = import_functions(ADREST_CONFIG['LOG_HANDLERS'])


class ResourceMetaClass(
    handler.HandlerMeta, throttle.ThrottleMeta, emitter.EmitterMeta,
        parser.ParserMeta, auth.AuthMeta):

    """ MetaClass for ResourceView. Create meta options. """

    def __new__(mcs, name, bases, params):

        # Run other meta classes
        cls = super(ResourceMetaClass, mcs).__new__(mcs, name, bases, params)

        meta = params.get('Meta')

        cls._meta.abstract = meta and getattr(meta, 'abstract', False)
        if cls._meta.abstract:
            return cls

        # Meta name (maybe precalculate in handler)
        cls._meta.name = cls._meta.name or ''.join(
            bit for bit in name.split('Resource') if bit).lower()

        # Prepare urls
        cls._meta.url_params = list(as_tuple(cls._meta.url_params))
        cls._meta.url_name = cls._meta.url_name or '-'.join(gen_url_name(cls))
        cls._meta.url_regex = cls._meta.url_regex or '/'.join(
            gen_url_regex(cls))

        return cls


class ResourceView(
    handler.HandlerMixin, throttle.ThrottleMixin, emitter.EmitterMixin,
        parser.ParserMixin, auth.AuthMixin, View):

    """ REST Resource. """

    # Create meta options
    __metaclass__ = ResourceMetaClass

    # Link to api if connected
    api = None

    # Instance's identifier
    identifier = None

    class Meta:

        # This abstract class
        abstract = True

        # Name (By default this set from model or class name)
        name = None

        # Save access log if ADRest logging is enabled
        log = True

        # Some custom URI params here
        url_params = None
        url_regex = None
        url_name = None

        # Custom prefix for url name and regex
        prefix = ''

        # If children object in hierarchy has FK=Null to parent,
        # allow to get this object (default: True)
        allow_public_access = False

    @csrf_exempt
    def dispatch(self, request, **resources):
        """ Try to dispatch the request.

        :return object: result

        """

        # Fix PUT and PATH methods in Django request
        request = fix_request(request)

        # Set self identifier
        self.identifier = request.META.get('REMOTE_ADDR', 'anonymous')

        # Send ADREST started signal
        api_request_started.send(self, request=request)

        # Send current api started signal
        if self.api:
            self.api.request_started.send(self, request=request)

        try:

            # Check request method
            self.check_method_allowed(request)

            # Authentificate
            self.authenticate(request)

            # Throttle check
            self.throttle_check()

            if request.method != 'OPTIONS' or not ADREST_CONFIG['ALLOW_OPTIONS']:

                # Parse content
                request.data = self.parse(request)

                # Get required resources
                resources = self.get_resources(
                    request, **resources)

                # Check owners
                self.check_owners(request, **resources)

                # Check rights for resources with this method
                self.check_rights(resources, request=request)

            response = self.handle_request(request, **resources)

            # Serialize response
            response = self.emit(response, request=request)

        except Exception as e:
            response = self.handle_exception(e, request=request)

        response["Allow"] = ', '.join(self._meta.allowed_methods)
        response["Vary"] = 'Authenticate, Accept'

        # Notify about errors
        self.notify_errors(request, response)

        # Save request to log handlers
        self.log_call(self, request=request, response=response, **resources)

        # Send finished signal
        api_request_finished.send(
            self, request=request, response=response, **resources)

        # Send finished signal in API context
        if self.api:
            self.api.request_finished.send(
                self, request=request, response=response, **resources)

        return response

    def check_owners(self, request, **resources):
        """ Check parents of current resource.

        Recursive scanning of the fact that the child has FK
        to the parent and in resources we have right objects.

        We check that in request like /author/1/book/2/page/3

        Page object with pk=3 has ForeignKey field linked to Book object
        with pk=2 and Book with pk=2 has ForeignKey field linked to Author
        object with pk=1.

        :return bool: If success else raise Exception

        """

        if self._meta.allow_public_access or not self._meta.parent:
            return True

        self.parent.check_owners(request, **resources)

        objects = resources.get(self._meta.name)
        if self._meta.model and self._meta.parent._meta.model and objects:
            pr = resources.get(self._meta.parent._meta.name)
            check = all(
                pr.pk == getattr(
                    o, "%s_id" % self._meta.parent._meta.name, None)
                for o in as_tuple(objects))

            if not pr or not check:
                # 403 Error if there is error in parent-children relationship
                raise HttpError(
                    "Access forbidden.", status=status.HTTP_403_FORBIDDEN)

        return True

    def handle_exception(self, e, request=None):
        """ Handle code exception.

        :param e: error instance
        :param request: :class:``django.http.HttpRequest`` instance
        :return response: Http response

        """
        if isinstance(e, HttpError):
            response = SerializedHttpResponse(e.content, status=e.status)
            return self.emit(
                response, request=request, emitter=e.emitter)

        if isinstance(e, (AssertionError, ValidationError)):

            content = unicode(e)

            if isinstance(e, FormError):
                content = e.form.errors

            response = SerializedHttpResponse(
                content, status=status.HTTP_400_BAD_REQUEST)

            return self.emit(response, request=request)

        if ADREST_CONFIG['DEBUG']:
            raise

        logger.exception('\nADREST API Error: %s', request.path)

        return HttpResponse(str(e), status=500)

    @classmethod
    def as_url(cls, api=None, name_prefix='', url_prefix=''):
        """ Generate url for resource.

        :return RegexURLPattern: Django URL

        """
        url_prefix = url_prefix and "%s/" % url_prefix
        name_prefix = name_prefix and "%s-" % name_prefix

        url_regex = '^%s%s/?$' % (
            url_prefix, cls._meta.url_regex.lstrip('^').rstrip('/$'))
        url_regex = url_regex.replace('//', '/')
        url_name = '%s%s' % (name_prefix, cls._meta.url_name)

        return url(url_regex, cls.as_view(api=api), name=url_name)


    @staticmethod
    def notify_errors(request, response):
        """Process response errors

        :param request: :class:``django.http.HttpRequest``
        :param response: :class:``django.http.HttpResponse``
        """
        if not response.status_code in ADREST_CONFIG['NOTIFY_ERRORS']:
            return False

        for notifier in NOTIFIERS:
            notifier(request, response)

    @staticmethod
    def log_call(self, request, response, **kwargs):
        """
        Send request data to handers

        :param self: resource instance
        :param request: :class:``django.http.HttpRequest``
        :param response: :class:``django.http.HttpResponse``
        :param \*\*kwargs\*\*: resources
        """

        for handler in LOG_HANDLERS:
            handler(self, request, response, **kwargs)



# pymode:lint_ignore=E1120,W0703,W0212
