from logging import getLogger

from django.core.exceptions import FieldError
from django.db.models import get_model, Model
from django.db.models.sql.constants import LOOKUP_SEP
from django.http import HttpResponse

from ..forms import PartitialForm
from ..settings import LIMIT_PER_PAGE
from ..utils import status, MetaOptions, UpdatedList
from ..utils.exceptions import HttpError
from ..utils.paginator import Paginator
from ..utils.tools import as_tuple


logger = getLogger('django.request')


class HandlerMeta(type):

    def __new__(mcs, name, bases, params):

        params['meta'] = params.get('meta', MetaOptions())
        cls = super(HandlerMeta, mcs).__new__(mcs, name, bases, params)

        # Create model from string
        if isinstance(cls.model, basestring):
            assert '.' in cls.model, ("'model_class' must be either a model"
                                      " or a model name in the format"
                                      " app_label.model_name")
            cls.model = get_model(*cls.model.split("."))

        # Check meta.name and queryset
        if cls.model:
            assert issubclass(cls.model, Model), "'model' attribute must be subclass of Model "
            cls.meta.name = cls.model._meta.module_name
            cls.meta.model_fields = set(f.name for f in cls.model._meta.fields)
            if cls.queryset is None:
                cls.queryset = cls.model.objects.all()

        # Create form if not exist
        if cls.model and not cls.form:
            class DynForm(PartitialForm):
                class Meta():
                    model = cls.model
                    fields = cls.form_fields
                    exclude = cls.form_exclude
            cls.form = DynForm

        return cls


class HandlerMixin(object):

    __metaclass__ = HandlerMeta

    limit_per_page = LIMIT_PER_PAGE
    model = None
    queryset = None
    form = None
    form_fields = None
    form_exclude = None
    callmap = {'GET': 'get', 'POST': 'post',
               'PUT': 'put', 'DELETE': 'delete',
               'PATCH': 'patch', 'OPTIONS': 'options',
               'HEAD': 'head'}

    def __init__(self, *args, **kwargs):
        " Copy self queryset for prevent query caching. "

        super(HandlerMixin, self).__init__(*args, **kwargs)

        if not self.queryset is None:
            self.queryset = self.queryset.all()

    @staticmethod
    def head(*args, **kwargs):
        " Default HEAD method. "

        return HttpResponse()

    def get(self, request, **resources):
        " Default GET method. Return instanse (collection) by model. "

        instance = resources.get(self.meta.name)
        if not instance is None:
            return instance

        return self.paginate(request, self.get_collection(request, **resources))

    def post(self, request, **resources):
        " Default POST method. Uses self form. "

        form = self.form(request.data, **resources)
        if form.is_valid():
            return form.save()

        raise HttpError(
            form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, **resources):
        " Default PUT method. Uses self form. Allow bulk update. "

        resource = resources.get(self.meta.name)
        if not resource:
            raise HttpError("Resource not found.", status=status.HTTP_404_NOT_FOUND)

        updated = UpdatedList()
        for o in as_tuple(resource):
            form = self.form(
                data=request.data, instance=o, **resources)

            if not form.is_valid():
                raise HttpError(
                    form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

            updated.append(form.save())

        return updated if len(updated) > 1 else updated[-1]

    def delete(self, request, **resources):
        " Default DELETE method. Allow bulk delete. "

        resource = resources.get(self.meta.name)
        if not resource:
            raise HttpError("Bad request", status=status.HTTP_404_NOT_FOUND)

        for o in as_tuple(resource):
            o.delete()

        return HttpResponse("")

    def patch(self, request, **resources):
        " Default PATCH method. Do nothing. "

        pass

    @staticmethod
    def options(request, **resources):
        " Default OPTIONS method. Always response OK. "

        return HttpResponse("OK")

    def get_collection(self, request, **resources):
        " Get filters and return filtered result. "

        if self.queryset is None:
            return None

        # Make filters from URL variables or resources
        default_filters = self.get_default_filters(**resources)
        filters = self.get_filters(request, **resources)
        filters.update(default_filters)

        # Get collection by queryset
        qs = self.queryset
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
        return dict((k, (v, False)) for k, v in resources.items() if k in self.meta.model_fields)

    def get_filters(self, request, **resources):
        " Make filters from GET variables. "

        filters = dict()
        for field in request.GET.iterkeys():
            tokens = field.split(LOOKUP_SEP)
            field_name = tokens[0]

            exclude = False
            if tokens[-1] == 'not':
                exclude = True
                tokens.pop()

            if not field_name in self.meta.model_fields:
                continue

            converter = self.model._meta.get_field(
                field_name).to_python if len(tokens) == 1 else lambda v: v
            value = map(converter, request.GET.getlist(field))

            if len(value) > 1:
                tokens.append('in')
            else:
                value = value.pop()

            filters[LOOKUP_SEP.join(tokens)] = (value, exclude)

        return filters

    def paginate(self, request, qs):
        " Paginate queryset. "

        return Paginator(request, qs, self.limit_per_page)


# pymode:lint_ignore=E1102
