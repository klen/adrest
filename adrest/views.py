#!/usr/bin/env python
# coding: utf-8
import sys
import traceback
from logging import getLogger

from django.conf.urls.defaults import url
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.core.mail import mail_admins
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .utils import status, MetaOptions, gen_url_name, gen_url_regex
from .utils.exceptions import HttpError
from .utils.paginator import Paginator
from .utils.tools import as_tuple
from adrest import settings
from adrest.mixin import auth, emitter, handler, parser, throttle
from adrest.signals import api_request_started, api_request_finished


logger = getLogger('django.request')


class ResourceMetaClass(handler.HandlerMeta, throttle.ThrottleMeta, emitter.EmitterMeta,
        parser.ParserMeta, auth.AuthMeta):
    """ MetaClass for ResourceView.
        Create meta options.
    """

    def __new__(mcs, name, bases, params):

        # Create meta if not exists
        params['meta'] = params.get('meta', MetaOptions())

        # Run other meta classes
        cls = super(ResourceMetaClass, mcs).__new__(mcs, name, bases, params)

        # Prepare allowed methods
        cls.allowed_methods = mcs.prepare_methods(cls.allowed_methods)

        # Check parent
        if cls.parent:
            try:
                cls.meta.parents += cls.parent.meta.parents + [cls.parent]
            except AttributeError:
                raise TypeError("%s.parent must be instance of %s" % (name, "ResourceView"))

        # Meta name (maybe precalculate in handler)
        cls.meta.name = cls.meta.name or cls.name or ''.join(bit for bit in name.split('Resource') if bit).lower()

        # Prepare urls
        cls.url_params = list(as_tuple(cls.url_params))
        cls.meta.url_name = cls.url_name or '-'.join(gen_url_name(cls))
        cls.meta.url_regex = cls.url_regex or '/'.join(gen_url_regex(cls))

        return cls

    @staticmethod
    def prepare_methods(methods):
        " Prepare allowed methods. "

        methods = as_tuple(methods)

        if not 'OPTIONS' in methods and settings.ALLOW_OPTIONS:
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

    # Create meta options
    __metaclass__ = ResourceMetaClass

    # Allowed methods
    allowed_methods = 'GET',

    # Name (Defaul by model name or class name)
    name = None

    # Link to api if connected
    api = None

    # Saves access log if enabled
    log = True

    # Link to parent resource
    parent = None

    # URL name and regex prefix
    prefix = ''

    # Some custom URI params here
    url_params = None
    url_regex = None
    url_name = None

    # If children object in hierarchy has FK=Null to parent, allow to get this
    # object (default: True)
    allow_public_access = False

    @csrf_exempt
    def dispatch(self, request, **resources):

        # Send started signal
        api_request_started.send(self, request = request)

        # Current HTTP method
        method = request.method.upper()

        try:

            # Check request method
            self.check_method_allowed(method)

            # Authentificate
            # We do not restrict access for OPTIONS request.
            if method == 'OPTIONS' and settings.ALLOW_OPTIONS:
                self.identifier = 'anonymous'
            else:
                self.identifier = self.authenticate(request)

            # Throttle check
            self.throttle_check()

            # Get required resources
            resources = self.get_resources(request, resource=self, **resources)

            # Check owners
            self.check_owners(**resources)

            # Check rights for resources with this method
            self.check_rights(resources, request=request)

            # Parse content
            if method in ('POST', 'PUT'):
                request.data = self.parse(request)
                if isinstance(request.data, basestring):
                    request.data = dict()

            # Get the appropriate create/read/update/delete function
            func = getattr(self, self.callmap.get(method, None))

            # Get function data
            content = func(request, **resources)

            # Serialize response
            response = self.emit(content, request=request)
            try:
                response["Allow"] = ', '.join(self.allowed_methods),
                response["Vary"] = 'Authenticate, Accept'

                # Add pagination headers
                # http://www.w3.org/Protocols/9707-link-header.html
                if isinstance(content, Paginator):
                    linked_resources = []
                    if content.next:
                        linked_resources.append('<%s>; rel="next"' % content.next)
                    if content.previous:
                        linked_resources.append('<%s>; rel="previous"' % content.previous)
                    response["Link"] = ", ".join(linked_resources)

            except TypeError:
                raise ValueError("Emitter must return HttpResponse")

        except (HttpError, AssertionError, ValidationError), e:
            response = HttpResponse(unicode(e), status=getattr(e, 'status', status.HTTP_400_BAD_REQUEST))
            response = self.emit(response, request=request)

        except Exception, e:
            response = self.handle_exception(e, request=request)

        errors_mail(response, request)

        # Send finished signal
        api_request_finished.send(self, request=request, response=response, **resources)

        return response

    @classmethod
    def check_method_allowed(cls, method):
        """ Ensure the request HTTP method is permitted for this resource, raising a ResourceException if it is not.
        """
        if not method in cls.callmap.keys():
            raise HttpError('Unknown or unsupported method \'%s\'' % method, status=status.HTTP_501_NOT_IMPLEMENTED)

        if not method in cls.allowed_methods:
            raise HttpError('Method \'%s\' not allowed on this resource.' % method, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @classmethod
    def get_resources(cls, request, resource=None, **resources):
        " Parse resource objects from URL and GET. "

        # Get from parent
        if cls.parent:
            resources = cls.parent.get_resources(request, resource=resource, **resources)

        pk = resources.get(cls.meta.name) or request.GET.get(cls.meta.name)
        if not cls.model or not pk:
            return resources

        try:
            resources[cls.meta.name] = cls.model.objects.get(pk = pk)

        except (ObjectDoesNotExist, ValueError):
            raise HttpError("Resource not found.", status=status.HTTP_404_NOT_FOUND)

        except MultipleObjectsReturned:
            raise HttpError("Resources conflict.", status=status.HTTP_409_CONFLICT)

        return resources

    @classmethod
    def check_owners(cls, **resources):
        """ Recursive scanning of the fact that the child has FK
            to the parent and in resources we have right objects.

            We check that in request like /author/1/book/2/page/3

            Page object with pk=3 has ForeignKey field linked to Book object with pk=2
            and Book with pk=2 has ForeignKey field linked to Author object with pk=1.
        """

        if cls.allow_public_access or not cls.parent:
            return True

        cls.parent.check_owners(**resources)

        resource = resources.get(cls.meta.name)
        if cls.model and cls.parent.model and resource:
            parent_resource = resources.get(cls.parent.meta.name)
            parent_resource_id = getattr(resource, "%s_id" % cls.parent.meta.name, None)
            try:
                assert parent_resource and parent_resource.pk == parent_resource_id
            except AssertionError:
                # 403 Error if there is error in parent-children relationship
                raise HttpError("Access forbidden.", status=status.HTTP_403_FORBIDDEN)

        return True

    @staticmethod
    def handle_exception(e, request=None, exc_info=None):
        """ Handle code exception.
        """
        if settings.DEBUG:
            raise

        logger.warning('ADREST API Error: %s' % request.path,
            exc_info=exc_info
        )

        return HttpResponse(str(e), status=500)

    @property
    def version(self):
        return str(self.api or '')

    @classmethod
    def as_url(cls, api=None, name_prefix='', url_prefix=''):
        " Generate url for resource. "
        url_prefix = url_prefix and "%s/" % url_prefix
        name_prefix = name_prefix and "%s-" % name_prefix

        url_regex = '^%s%s/?$' % (url_prefix, cls.meta.url_regex.lstrip('^').rstrip('/$'))
        url_regex = url_regex.replace('//', '/')
        url_name = '%s%s' % (name_prefix, cls.meta.url_name)

        return url(url_regex, cls.as_view(api=api), name = url_name)


def errors_mail(response, request):

    if not response.status_code in settings.MAIL_ERRORS:
        return False

    subject = 'ADREST API Error (%s): %s' % (response.status_code, request.path)
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
