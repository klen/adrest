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

from .mixin import auth, emitter, handler, parser, throttle
from .settings import ALLOW_OPTIONS, DEBUG, MAIL_ERRORS
from .signals import api_request_started, api_request_finished
from .utils import status, MetaOptions
from .utils.exceptions import HttpError
from .utils.response import SerializedHttpResponse
from .utils.tools import as_tuple, gen_url_name, gen_url_regex, fix_request


logger = getLogger('django.request')


class ResourceMetaClass(
    handler.HandlerMeta, throttle.ThrottleMeta, emitter.EmitterMeta,
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
                raise TypeError("%s.parent must be instance of %s" %
                                (name, "ResourceView"))

        # Meta name (maybe precalculate in handler)
        cls.meta.name = cls.meta.name or cls.name or ''.join(
            bit for bit in name.split('Resource') if bit).lower()

        # Prepare urls
        cls.url_params = list(as_tuple(cls.url_params))
        cls.meta.url_name = cls.url_name or '-'.join(gen_url_name(cls))
        cls.meta.url_regex = cls.url_regex or '/'.join(gen_url_regex(cls))

        return cls

    @staticmethod
    def prepare_methods(methods):
        " Prepare allowed methods. "

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

    # Create meta options
    __metaclass__ = ResourceMetaClass

    # Allowed methods
    allowed_methods = 'GET',

    # Name (By default this set from model or class name)
    name = None

    # Link to api if connected
    api = None

    # Saves access log if enabled
    log = True

    # Link to parent resource
    parent = None

    # Custom prefix for url name and regex
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

        # Fix PUT and PATH methods in Django request
        request = fix_request(request)

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
            response["Allow"] = ', '.join(self.allowed_methods)
            response["Vary"] = 'Authenticate, Accept'

        except HttpError, e:
            response = SerializedHttpResponse(e.content, status=e.status)
            response = self.emit(
                response, request=request, emitter=e.emitter)

        except (AssertionError, ValidationError), e:
            response = SerializedHttpResponse(
                unicode(e), status=status.HTTP_400_BAD_REQUEST)
            response = self.emit(response, request=request)

        except Exception, e:
            response = self.handle_exception(e, request=request)

        # Send errors on mail
        errors_mail(response, request)

        # Send finished signal
        api_request_finished.send(
            self, request=request, response=response, **resources)

        # Send finished signal in API context
        if self.api:
            self.api.request_finished.send(self, request=request, response=response, **resources)

        return response

    def handle_request(self, request, **resources):

        # Get the appropriate create/read/update/delete function
        view = getattr(self, self.callmap[request.method])

        # Get function data
        return view(request, **resources)

    @classmethod
    def check_method_allowed(cls, method):
        """ Ensure the request HTTP method is permitted for this resource, raising a ResourceException if it is not.
        """
        if not method in cls.callmap.keys():
            raise HttpError('Unknown or unsupported method \'%s\'' % method,
                            status=status.HTTP_501_NOT_IMPLEMENTED)

        if not method in cls.allowed_methods:
            raise HttpError(
                'Method \'%s\' not allowed on this resource.' % method,
                status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @classmethod
    def get_resources(cls, request, resource=None, **resources):
        " Parse resource objects from URL and GET. "

        if cls.parent:
            resources = cls.parent.get_resources(request, resource=resource, **resources)

        pks = resources.get(
            cls.meta.name) or request.REQUEST.getlist(cls.meta.name)

        if not pks or cls.queryset is None:
            return resources

        pks = as_tuple(pks)

        try:
            if len(pks) == 1:
                resources[cls.meta.name] = cls.queryset.get(pk=pks[0])

            else:
                resources[cls.meta.name] = cls.queryset.filter(pk__in=pks)

        except (ObjectDoesNotExist, ValueError, AssertionError):
            raise HttpError("Resource not found.",
                            status=status.HTTP_404_NOT_FOUND)

        except MultipleObjectsReturned:
            raise HttpError("Resources conflict.",
                            status=status.HTTP_409_CONFLICT)

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

        objects = resources.get(cls.meta.name)
        if cls.model and cls.parent.model and objects:
            try:
                pr = resources.get(cls.parent.meta.name)
                assert pr and all(pr.pk == getattr(
                    o, "%s_id" % cls.parent.meta.name, None) for o in as_tuple(objects))
            except AssertionError:
                # 403 Error if there is error in parent-children relationship
                raise HttpError(
                    "Access forbidden.", status=status.HTTP_403_FORBIDDEN)

        return True

    @staticmethod
    def handle_exception(e, request=None):
        """ Handle code exception.
        """
        if DEBUG:
            raise

        logger.exception('\nADREST API Error: %s' % request.path)

        return HttpResponse(str(e), status=500)

    @property
    def version(self):
        return str(self.api or '')

    @classmethod
    def as_url(cls, api=None, name_prefix='', url_prefix=''):
        " Generate url for resource. "
        url_prefix = url_prefix and "%s/" % url_prefix
        name_prefix = name_prefix and "%s-" % name_prefix

        url_regex = '^%s%s/?$' % (
            url_prefix, cls.meta.url_regex.lstrip('^').rstrip('/$'))
        url_regex = url_regex.replace('//', '/')
        url_name = '%s%s' % (name_prefix, cls.meta.url_name)

        return url(url_regex, cls.as_view(api=api), name=url_name)

    def get_name(self):
        return self.meta.name


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

# pymode:lint_ignore=E1120
