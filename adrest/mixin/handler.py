""" Implement REST functionality. """
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse
from logging import getLogger

from ..forms import PartitialForm
from ..settings import ADREST_ALLOW_OPTIONS
from ..utils import status, UpdatedList
from ..utils.exceptions import HttpError, FormError
from ..utils.tools import as_tuple
from .dynamic import DynamicMixin, DynamicMixinMeta


__all__ = 'HandlerMixin',

logger = getLogger('django.request')


__all__ = 'HandlerMixin',


class Meta:

    """ Handler options. Setup parameters for REST implementation.

    ::

        class SomeResource(HandlerMixin, View):

            class Meta:
                allowed_methods = 'get', 'post'
                model = 'app.model'

    """

    #: List of allowed methods (or simple one)
    allowed_methods = 'GET',

    #: Map HTTP methods to handler methods
    callmap = dict(
        (m.upper(), m) for m in (
            'get', 'post', 'put', 'delete', 'patch', 'options', 'head')
    )

    #: Set form for resource by manual
    form = None

    #: Specify field's names for automatic a model form
    form_fields = None

    #: Exclude field's names for automatic a model form
    form_exclude = None


class HandlerMeta(DynamicMixinMeta):

    """ Prepare handler class. """

    def __new__(mcs, name, bases, params):

        cls = super(HandlerMeta, mcs).__new__(mcs, name, bases, params)

        # Prepare allowed methods
        cls._meta.allowed_methods = mcs.__prepare_methods(
            cls._meta.allowed_methods)

        if not cls._meta.model:
            return cls

        cls._meta.name = cls._meta.name or cls._meta.model._meta.module_name

        # Create form if not exist
        if not cls._meta.form:

            class DynForm(PartitialForm):

                class Meta:
                    model = cls._meta.model
                    fields = cls._meta.form_fields
                    exclude = cls._meta.form_exclude

            cls._meta.form = DynForm

        return cls

    @staticmethod
    def __prepare_methods(methods):

        methods = tuple([str(m).upper() for m in as_tuple(methods)])

        if not 'OPTIONS' in methods and ADREST_ALLOW_OPTIONS:
            methods += 'OPTIONS',

        if not 'HEAD' in methods and 'GET' in methods:
            methods += 'HEAD',

        return methods


class HandlerMixin(DynamicMixin):

    """ Implement REST API.


    .. autoclass:: adrest.mixin.handler.Meta
       :members:

    Example: ::

        class SomeResource(HandlerMixin, View):

            class Meta:
                allowed_methods = 'get', 'post'
                model = 'app.model'

            def dispatch(self, request, **resources):

                self.check_method_allowed(request)

                resources = self.get_resources(request, **resources)

                return self.handle_request(request, **resources)

    """

    __metaclass__ = HandlerMeta

    Meta = Meta

    def handle_request(self, request, **resources):
        """ Get a method for request and execute.

        :return object: method result

        """
        if not request.method in self._meta.callmap.keys():
            raise HttpError(
                'Unknown or unsupported method \'%s\'' % request.method,
                status=status.HTTP_501_NOT_IMPLEMENTED)

        # Get the appropriate create/read/update/delete function
        view = getattr(self, self._meta.callmap[request.method])

        # Get function data
        return view(request, **resources)

    @staticmethod
    def head(*args, **kwargs):
        """ Just return empty response.

        :return django.http.Response: empty response.

        """

        return HttpResponse()

    def get(self, request, **resources):
        """ Default GET method. Return instance (collection) by model.

        :return object: instance or collection from self model

        """

        instance = resources.get(self._meta.name)
        if not instance is None:
            return instance

        return self.paginate(
            request, self.get_collection(request, **resources))

    def post(self, request, **resources):
        """ Default POST method. Uses the handler's form.

        :return object: saved instance or raise form's error

        """
        if not self._meta.form:
            return None

        form = self._meta.form(request.data, **resources)
        if form.is_valid():
            return form.save()

        raise FormError(form)

    def put(self, request, **resources):
        """ Default PUT method. Uses self form. Allow bulk update.

        :return object: changed instance or raise form's error

        """
        if not self._meta.form:
            return None

        if not self._meta.name in resources or not resources[self._meta.name]:
            raise HttpError(
                "Resource not found.", status=status.HTTP_404_NOT_FOUND)
        resource = resources.pop(self._meta.name)

        updated = UpdatedList()
        for o in as_tuple(resource):
            form = self._meta.form(data=request.data, instance=o, **resources)

            if not form.is_valid():
                raise FormError(form)

            updated.append(form.save())

        return updated if len(updated) > 1 else updated[-1]

    def delete(self, request, **resources):
        """ Default DELETE method. Allow bulk delete.

        :return django.http.response: empty response

        """

        resource = resources.get(self._meta.name)
        if not resource:
            raise HttpError("Bad request", status=status.HTTP_404_NOT_FOUND)

        for o in as_tuple(resource):
            o.delete()

        return HttpResponse("")

    def patch(self, request, **resources):
        """ Default PATCH method.

        :return object: changed instance or raise form's error

        """
        return self.put(request, **resources)

    @staticmethod
    def options(request, **resources):
        """ Default OPTIONS method.

        :return django.http.response: 'OK' response

        """

        return HttpResponse("OK")

    @classmethod
    def check_method_allowed(cls, request):
        """ Ensure the request HTTP method is permitted for this resource.

        Raising a ResourceException if it is not.

        """
        if not request.method in cls._meta.allowed_methods:
            raise HttpError(
                'Method \'%s\' not allowed on this resource.' % request.method,
                status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def get_resources(self, request, **resources):
        """ Parse resource objects from URL and request.

        :return dict: Resources.

        """

        if self.parent:
            resources = self.parent.get_resources(request, **resources)

        pks = (
            resources.get(self._meta.name) or
            request.REQUEST.getlist(self._meta.name) or
            getattr(request, 'data', None) and request.data.get(
                self._meta.name))

        if not pks or self._meta.queryset is None:
            return resources

        pks = as_tuple(pks)

        try:
            if len(pks) == 1:
                resources[self._meta.name] = self._meta.queryset.get(pk=pks[0])

            else:
                resources[self._meta.name] = self._meta.queryset.filter(
                    pk__in=pks)

        except (ObjectDoesNotExist, ValueError, AssertionError):
            raise HttpError("Resource not found.",
                            status=status.HTTP_404_NOT_FOUND)

        except MultipleObjectsReturned:
            raise HttpError("Resources conflict.",
                            status=status.HTTP_409_CONFLICT)

        return resources


# pymode:lint_ignore=E1102,W0212,R0924
