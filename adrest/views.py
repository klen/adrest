#!/usr/bin/env python
# coding: utf-8
import logging
import traceback

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.forms.models import ModelChoiceField
from django.utils.encoding import smart_unicode
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import HttpResponse

from .utils import status, MetaOptions
from .utils.auth import AnonimousAuthenticator
from .utils.emitter import HTMLTemplateEmitter, JSONEmitter
from .utils.exceptions import HttpError
from .utils.tools import as_tuple
from adrest import settings
from adrest.mixin import auth, emitter, handler, parser, throttle
from adrest.signals import api_request_started, api_request_finished


LOG = logging.getLogger('adrest')


class ResourceMetaClass(handler.HandlerMeta, throttle.ThrottleMeta, emitter.EmitterMeta,
        parser.ParserMeta, auth.AuthMeta):
    """ MetaClass for ResourceView.
        Create meta options.
    """

    def __new__(mcs, name, bases, params):
        params['meta'] = params.get('meta', MetaOptions())

        cls = super(ResourceMetaClass, mcs).__new__(mcs, name, bases, params)
        cls.allowed_methods = as_tuple(cls.allowed_methods)
        if settings.ALLOW_OPTIONS:
            cls.allowed_methods += 'OPTIONS',

        if cls.parent:
            try:
                cls.meta.parents += cls.parent.meta.parents + [cls.parent]
            except AttributeError:
                raise TypeError("%s.parent must be instance of %s" % (name, "ResourceView"))

        cls.meta.name = cls.meta.name or cls.name or ''.join(bit for bit in name.split('Resource') if bit).lower()
        uri_params = cls.uri_params or []
        cls.meta.urlname = '-'.join(
                ([cls.parent.meta.urlname] if cls.parent else []) +
                ([ cls.prefix ] if cls.prefix else []) +
                list(uri_params) +
                [cls.meta.name])
        cls.meta.urlregex = '/'.join(
                '%(name)s/(?P<%(name)s>[^/]+)' % dict(name = p)
                for p in (
                    [p.meta.name for p in cls.meta.parents] + list(uri_params)))
        cls.meta.urlregex = cls.meta.urlregex + '/' if cls.meta.urlregex else ''
        if cls.prefix:
            cls.meta.urlregex = '%s%s/' % (cls.meta.urlregex, cls.prefix)
        cls.meta.urlregex += '%(name)s/(?:(?P<%(name)s>[^/]+)/)?$' % dict(
                name = cls.meta.name)

        cls.meta.models = [o.model for o in cls.meta.parents + [ cls ] if o.model]
        return cls


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
    uri_params = None

    # If children object in hierarchy has FK=Null to parent, allow to get this
    # object (default: True)
    allow_public_access = False

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):

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
            resources = self.get_resources_from_uri(**kwargs)

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
            content = func(request, *args, **resources)

            # Serialize response
            response = self.emit(content, request=request)
            try:
                response["Allow"] = ', '.join(self.allowed_methods),
                response["Vary"] = 'Authenticate, Accept'

            except TypeError:
                raise ValueError("Emitter must return HttpResponse")

        except (HttpError, AssertionError, ValidationError), e:
            content = HttpResponse(unicode(e), status=getattr(e, 'status', status.HTTP_400_BAD_REQUEST))
            response = self.emit(content, request=request)

        except Exception, e:
            response = self.handle_exception(e)

        # Send finished signal
        api_request_finished.send(self, request=request, response=response)

        return response

    def check_method_allowed(self, method):
        """ Ensure the request HTTP method is permitted for this resource, raising a ResourceException if it is not.
        """
        if not method in self.callmap.keys():
            raise HttpError('Unknown or unsupported method \'%s\'' % method, status=status.HTTP_501_NOT_IMPLEMENTED)

        if not method in self.allowed_methods:
            raise HttpError('Method \'%s\' not allowed on this resource.' % method, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_resources_from_uri(self, **resources):
        """ Parse form params from URI.

            For example, /author/1/book/2 converted to resources array with ORM
            objects Book with pk=2 and Author with pk=1

        """

        # Generate pairs (model_name, model_class) and convert it to dictionary
        mdict = dict((m._meta.module_name, m) for m in self.meta.models)

        # URL objects
        for key, value in resources.iteritems():
            key = key.lower()
            # If recource view associated with this model and we have its value
            # in URI -- try to convert it in real ORM object
            if mdict.has_key(key) and value:
                try:
                    resources[key] = mdict.get(key).objects.get(pk=value)

                except (ObjectDoesNotExist, ValueError):
                    raise HttpError("Resource not found.", status=status.HTTP_404_NOT_FOUND)

                except MultipleObjectsReturned:
                    raise HttpError("Resources conflict.", status=status.HTTP_409_CONFLICT)

        # If we get ORM object resource with model_name like this resource model
        # name, add it to resource as "instance"
        # For example: ResourceView.model=Author, request was /author/1/
        # resources['instance'] = Author_object_with_pk=1
        instance = resources.get(self.meta.name)
        if instance:
            resources['instance'] = instance
        return resources

    def check_owners(self, **resources):
        """ Recursive scanning of the fact that the child has FK
            to the parent and in resources we have right objects.

            We check that in request like /author/1/book/2/page/3

            Page object with pk=3 has ForeignKey field linked to Book object with pk=2
            and Book with pk=2 has ForeignKey field linked to Author object with pk=1.
        """

        # Build iterator with all models for this Resource
        # Models list generated automatically based on "parent" and "model field
        # in Resource description
        it = reversed( [m._meta.module_name for m in self.meta.models] )
        try:
            # Get two models names
            c_name, f_name = next(it), next(it)

            while True:
                # Get objects from resources array for two models
                ofm, ocm = resources.get(f_name), resources.get(c_name)

                # Test parent element linked from children
                # If children haven't link to parent and it's allowed by allow_public_access -- it's ok, object available for public
                # If children have FK field named as parent model and it's value equivalent to
                #   object in resources -- it's OK
                # ELSE -- it's not ok, stop check!
                parent_in_child = getattr(ocm, '%s_id' % f_name, None)
                assert (not ocm) or \
                       (self.allow_public_access and self.allow_public_access == c_name and not parent_in_child) or \
                       (parent_in_child and ofm and parent_in_child == ofm.pk)

                # Swap and get one more model name from iterator
                f_name, c_name = next(it), f_name

        except (AssertionError, ObjectDoesNotExist):
            # 403 Error if there is error in parent-children relationship
            raise HttpError("Access forbidden.", status=status.HTTP_403_FORBIDDEN)

        except StopIteration:
            pass

        return True

    @staticmethod
    def handle_exception(e):
        """ Handle code exception.
        """
        if settings.DEBUG:
            raise

        else:
            traceback.print_exc()
            LOG.error(str(e))
            return HttpResponse(str(e), status=500)

    @property
    def version(self):
        return str(self.api or '')


class ApiMapResource(ResourceView):
    """ Simple JSON Api Map.
    """
    log = False
    emitters = HTMLTemplateEmitter, JSONEmitter
    authenticators = AnonimousAuthenticator
    template = 'api/apimap.html'

    def get(self, *args, **Kwargs):
        api_map = []
        for key, rinfo in sorted(self.api._map.iteritems(), key=lambda x: x[1].get('urlregex')):
            rinfo = self.api._map[key]
            r = rinfo['resource']

            result = dict(
                name = rinfo['urlname'],
                methods = r.allowed_methods,
                fields = []
            )

            if r.model:
                result['resource'] = r.model.__name__

            form = r.form
            if form and ('POST' in r.allowed_methods or 'PUT' in r.allowed_methods):
                result['fields'] += [
                    (name, dict(required = f.required and f.initial is None, help = smart_unicode(f.help_text + '')))
                        for name, f in form.base_fields.iteritems()
                        if not (isinstance(f, ModelChoiceField) and f.choices.queryset.model in r.meta.models)
                ]
            key = rinfo['urlregex'].replace("(?P", "").replace("[^/]+)", "").replace("?:", "").replace("$", "")

            authenticators = as_tuple(rinfo['params'].get('authenticators') or r.authenticators)

            for a in authenticators:
                result['fields'] += a.get_fields()

            result['auth'] = set(map(str, authenticators))

            api_map.append((key, result))

        return (self.api.str_version, api_map)
