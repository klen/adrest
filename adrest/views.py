#!/usr/bin/env python
# coding: utf-8
import logging

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.base import ModelBase, Model
from django.db.models import get_model
from django.forms.models import ModelChoiceField
from django.utils.encoding import smart_unicode
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .utils import status
from .utils.auth import AnonimousAuthenticator
from .utils.emitter import HTMLTemplateEmitter, JSONEmitter
from .utils.exceptions import HttpError
from .utils.response import Response
from .utils.tools import as_tuple
from adrest import settings
from adrest.mixin import ThrottleMixin, ParserMixin, HandlerMixin, EmitterMixin, AuthenticatorMixin
from adrest.signals import api_request_started, api_request_finished


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
            if isinstance(cls.model, basestring):
                assert '.' in cls.model, ("'model_class' must be either a model"
                                        " or a model name in the format"
                                        " app_label.model_name")
                cls.model = get_model(*cls.model.split("."))

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

    allowed_methods = 'GET',

    # If children object in hierarchy has FK=Null to parent, allow to get this
    # object (default: True)
    allow_public_access = False

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
            if method == 'OPTIONS' and settings.ALLOW_OPTIONS:
                self.identifier = 'anonymous'
            else:
                self.identifier = self.authenticate()

            # Throttle check
            self.throttle_check()

            # Get required resources
            resources = self.get_resources_from_uri(**kwargs)

            # Check owners
            self.check_owners(**resources)

            # Check rights for resources with this method
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
            LOG.error(str(e))
            return Response(str(e), status=500)

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

            form = r.get_form()
            if form and ('POST' in r.allowed_methods or 'PUT' in r.allowed_methods):
                result['fields'] += [
                    (name, dict(required = f.required and f.initial is None, help = smart_unicode(f.help_text + '')))
                        for name, f in form.base_fields.iteritems()
                        if not (isinstance(f, ModelChoiceField) and f.choices.queryset.model in r.meta.models)
                ]
            key = rinfo['urlregex'].replace("(?P", "").replace("[^/]+)", "").replace("?:", "").replace("$", "")

            authenticators = as_tuple(
                rinfo['kwargs'].get('authenticators')
                or self.api.kwargs.get('authenticators')
                or r.authenticators
            )

            for a in authenticators:
                result['fields'] += a.get_fields()

            result['auth'] = set(map(str, authenticators))

            api_map.append((key, result))

        return (self.api.str_version, api_map)


# Since we handle cross-origin XML HTTP requests, let OPTIONS be another
# default allowed method.
if settings.ALLOW_OPTIONS:
    ResourceView.allowed_methods += 'OPTIONS',
