""" Implement REST functionality. """
from logging import getLogger

from django.core.exceptions import FieldError
from django.db.models import get_model, Model
from django.http import HttpResponse

from ..forms import PartitialForm
from ..settings import LIMIT_PER_PAGE
from ..utils import status, UpdatedList
from ..utils.meta import MetaBase
from ..utils.exceptions import HttpError, FormError
from ..utils.paginator import Paginator
from ..utils.tools import as_tuple


__all__ = 'HandlerMixin',

# Separator used to split filter strings apart.
LOOKUP_SEP = '__'

logger = getLogger('django.request')


class HandlerMeta(MetaBase):

    """ Prepare handler class. """

    def __new__(mcs, name, bases, params):

        cls = super(HandlerMeta, mcs).__new__(mcs, name, bases, params)

        if not cls._meta.model:
            return cls

        # Create model from string
        if isinstance(cls._meta.model, basestring):
            assert '.' in cls._meta.model, (
                "'model_class' must be either a model"
                " or a model name in the format"
                " app_label.model_name")
            cls._meta.model = get_model(*cls._meta.model.split("."))

        # Check meta.name and queryset
        assert issubclass(
            cls._meta.model, Model), \
            "'model' attribute must be subclass of Model "

        cls._meta.name = cls._meta.name or cls._meta.model._meta.module_name

        cls._meta.model_fields = set(
            f.name for f in cls._meta.model._meta.fields)
        if cls._meta.queryset is None:
            cls._meta.queryset = cls._meta.model.objects.all()

        # Create form if not exist
        if not cls._meta.form:

            class DynForm(PartitialForm):

                class Meta:
                    model = cls._meta.model
                    fields = cls._meta.form_fields
                    exclude = cls._meta.form_exclude

            cls._meta.form = DynForm

        return cls


class HandlerMixin(object):

    """ REST handler. """

    __metaclass__ = HandlerMeta

    class Meta:
        callmap = dict(
            (m.upper(), m) for m in (
                'get', 'post', 'put', 'delete', 'patch', 'options', 'head')
        )
        limit_per_page = LIMIT_PER_PAGE
        model = None
        queryset = None
        form = None
        form_fields = None
        form_exclude = None

    def __init__(self, *args, **kwargs):
        """ Copy self queryset for prevent query caching. """

        super(HandlerMixin, self).__init__(*args, **kwargs)

        if not self._meta.queryset is None:
            self._meta.queryset = self._meta.queryset.all()

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

    def get_collection(self, request, **resources):
        """ Get filters and return filtered result.

        :return collection: collection of related resources.

        """

        if self._meta.queryset is None:
            return []

        # Make filters from URL variables or resources
        default_filters = self.get_default_filters(**resources)
        filters = self.get_filters(request, **resources)
        filters.update(default_filters)

        # Get collection by queryset
        qs = self._meta.queryset
        for key, (value, exclude) in filters.items():
            try:
                if exclude:
                    qs = qs.exclude(**{key: value})

                else:
                    qs = qs.filter(**{key: value})
            except FieldError, e:
                logger.warning(e)

        return qs

    def get_default_filters(self, **resources):
        """ Return default filters by a model fields.

        :return dict: name, field

        """
        return dict(
            (k, (v, False))
            for k, v in resources.items()
            if k in self._meta.model_fields)

    def get_filters(self, request, **resources):
        """ Make filters from GET variables.

        :return dict: filters

        """

        filters = dict()
        for field in request.GET.iterkeys():
            tokens = field.split(LOOKUP_SEP)
            field_name = tokens[0]

            exclude = False
            if tokens[-1] == 'not':
                exclude = True
                tokens.pop()

            if not field_name in self._meta.model_fields:
                continue

            converter = self._meta.model._meta.get_field(
                field_name).to_python if len(tokens) == 1 else lambda v: v
            value = map(converter, request.GET.getlist(field))

            if len(value) > 1:
                tokens.append('in')
            else:
                value = value.pop()

            filters[LOOKUP_SEP.join(tokens)] = (value, exclude)

        return filters

    def paginate(self, request, collection):
        """ Paginate collection.

        :return object: Collection or paginator

        """
        p = Paginator(request, collection, self._meta.limit_per_page)
        return p.paginator and p or UpdatedList(collection)


# pymode:lint_ignore=E1102,W0212,R0924
