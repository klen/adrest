""" Base request resource. """
import sys
import traceback
from logging import getLogger

from django.conf.urls.defaults import url
from django.core.exceptions import (
    ObjectDoesNotExist, MultipleObjectsReturned, ValidationError)
from django.core.mail import mail_admins
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .mixin import auth, emitter, handler, parser, throttle
from .settings import ALLOW_OPTIONS, DEBUG, MAIL_ERRORS
from .signals import api_request_started, api_request_finished
from .utils import status
from .utils.exceptions import HttpError, FormError
from .utils.response import SerializedHttpResponse
from .utils.tools import as_tuple, gen_url_name, gen_url_regex, fix_request


logger = getLogger('django.request')


__all__ = 'ResourceView',


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

        # Prepare allowed methods
        cls._meta.allowed_methods = mcs.__prepare_methods(
            cls._meta.allowed_methods)

        # Check parent
        cls._meta.parents = cls._meta.parents or []
        if cls._meta.parent:
            try:
                cls._meta.parents += cls._meta.parent._meta.parents + [
                    cls._meta.parent]
            except AttributeError:
                raise TypeError("%s.Meta.parent must be instance of %s" %
                                (name, "ResourceView"))

        # Meta name (maybe precalculate in handler)
        cls._meta.name = cls._meta.name or ''.join(
            bit for bit in name.split('Resource') if bit).lower()

        # Prepare urls
        cls._meta.url_params = list(as_tuple(cls._meta.url_params))
        cls._meta.url_name = cls._meta.url_name or '-'.join(gen_url_name(cls))
        cls._meta.url_regex = cls._meta.url_regex or '/'.join(
            gen_url_regex(cls))

        return cls

    @staticmethod
    def __prepare_methods(methods):

        methods = tuple([str(m).upper() for m in as_tuple(methods)])

        if not 'OPTIONS' in methods and ALLOW_OPTIONS:
            methods += 'OPTIONS',

        if not 'HEAD' in methods and 'GET' in methods:
            methods += 'HEAD',

        return methods


class ResourceView(handler.HandlerMixin,
                   throttle.ThrottleMixin,
                   emitter.EmitterMixin,
                   parser.ParserMixin,
                   auth.AuthMixin,
                   View):

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

        # Allowed methods
        allowed_methods = 'GET',

        # Name (By default this set from model or class name)
        name = None

        # Save access log if ADRest logging is enabled
        log = True

        # Link to parent resource
        parent = None

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
            self.check_method_allowed(request.method)

            # Authentificate
            self.authenticate(request)

            # Throttle check
            self.throttle_check()

            if request.method != 'OPTIONS' or not ALLOW_OPTIONS:

                # Get required resources
                resources = self.get_resources(
                    request, resource=self, **resources)

                # Check owners
                self.check_owners(**resources)

                # Check rights for resources with this method
                self.check_rights(resources, request=request)

                # Parse content
                request.data = self.parse(request)

            response = self.handle_request(request, **resources)

            # Serialize response
            response = self.emit(response, request=request)

        except Exception as e:
            response = self.handle_exception(e, request=request)

        response["Allow"] = ', '.join(self._meta.allowed_methods)
        response["Vary"] = 'Authenticate, Accept'

        # Send errors on mail
        errors_mail(response, request)

        # Send finished signal
        api_request_finished.send(
            self, request=request, response=response, **resources)

        # Send finished signal in API context
        if self.api:
            self.api.request_finished.send(
                self, request=request, response=response, **resources)

        return response

    @classmethod
    def check_method_allowed(cls, method):
        """ Ensure the request HTTP method is permitted for this resource.

        Raising a ResourceException if it is not.

        """
        if not method in cls._meta.allowed_methods:
            raise HttpError(
                'Method \'%s\' not allowed on this resource.' % method,
                status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @classmethod
    def get_resources(cls, request, resource=None, **resources):
        """ Parse resource objects from URL.

        :return dict: Resources.

        """

        if cls._meta.parent:
            resources = cls._meta.parent.get_resources(
                request, resource=resource, **resources)

        pks = resources.get(
            cls._meta.name) or request.REQUEST.getlist(cls._meta.name)

        if not pks or cls._meta.queryset is None:
            return resources

        pks = as_tuple(pks)

        try:
            if len(pks) == 1:
                resources[cls._meta.name] = cls._meta.queryset.get(pk=pks[0])

            else:
                resources[cls._meta.name] = cls._meta.queryset.filter(
                    pk__in=pks)

        except (ObjectDoesNotExist, ValueError, AssertionError):
            raise HttpError("Resource not found.",
                            status=status.HTTP_404_NOT_FOUND)

        except MultipleObjectsReturned:
            raise HttpError("Resources conflict.",
                            status=status.HTTP_409_CONFLICT)

        return resources

    @classmethod
    def check_owners(cls, **resources):
        """ Check parents of current resource.

        Recursive scanning of the fact that the child has FK
        to the parent and in resources we have right objects.

        We check that in request like /author/1/book/2/page/3

        Page object with pk=3 has ForeignKey field linked to Book object
        with pk=2 and Book with pk=2 has ForeignKey field linked to Author
        object with pk=1.

        :return bool: If success else raise Exception

        """

        if cls._meta.allow_public_access or not cls._meta.parent:
            return True

        cls._meta.parent.check_owners(**resources)

        objects = resources.get(cls._meta.name)
        if cls._meta.model and cls._meta.parent._meta.model and objects:
            try:
                pr = resources.get(cls._meta.parent._meta.name)
                assert pr and all(
                    pr.pk == getattr(
                        o, "%s_id" % cls._meta.parent._meta.name, None)
                    for o in as_tuple(objects))
            except AssertionError:
                # 403 Error if there is error in parent-children relationship
                raise HttpError(
                    "Access forbidden.", status=status.HTTP_403_FORBIDDEN)

        return True

    def handle_exception(self, e, request=None):
        """ Handle code exception.
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

        if DEBUG:
            raise

        logger.exception('\nADREST API Error: %s', request.path)

        return HttpResponse(str(e), status=500)

    @property
    def version(self):
        return str(self.api or '')

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


def errors_mail(response, request):

    if not response.status_code in MAIL_ERRORS:
        return False

    subject = 'ADREST API Error (%s): %s' % (
        response.status_code, request.path)
    stack_trace = '\n'.join(traceback.format_exception(*sys.exc_info()))
    message = """
Stacktrace:
===========
%s

Handler data:
=============
%s

Request information:
====================
%s

""" % (stack_trace, repr(getattr(request, 'data', None)), repr(request))
    return mail_admins(subject, message, fail_silently=True)

# pymode:lint_ignore=E1120,W0703
