from copy import deepcopy
from django.db.models import get_model, Model
from logging import getLogger
from django.db.models.sql.constants import LOOKUP_SEP
from django.core.exceptions import FieldError
from django.http import HttpResponse

from adrest.forms import PartitialForm
from adrest.settings import LIMIT_PER_PAGE
from adrest.utils import status, MetaOptions
from adrest.utils.exceptions import HttpError
from adrest.utils.paginator import Paginator


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
    callmap = { 'GET': 'get', 'POST': 'post',
                'PUT': 'put', 'DELETE': 'delete',
                'OPTIONS': 'options', 'HEAD': 'head' }

    def __init__(self, *args, **kwargs):
        super(HandlerMixin, self).__init__(*args, **kwargs)
        # Copy self queryset for prevent query caching
        if not self.queryset is None:
            self.queryset = self.queryset.all()

    @staticmethod
    def head(*args, **kwargs):
        return HttpResponse()

    def get(self, request, **resources):
        assert self.model, "This auto method required in model."
        instance = resources.get(self.meta.name)
        if instance:
            return instance

        return self.paginate(request, self.get_queryset(request, **resources))

    def post(self, request, **resources):
        form = self.form(data=deepcopy(request.data), **resources)
        if form.is_valid():
            return form.save()
        raise HttpError(form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, **resources):
        instance = resources.get(self.meta.name)
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_404_NOT_FOUND)

        form = self.form(data=deepcopy(request.data), instance=instance, **resources)
        if form.is_valid():
            return form.save()

        raise HttpError(form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **resources):
        instance = resources.get(self.meta.name)
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_400_BAD_REQUEST)

        for name, owner in resources.items():
            if hasattr(instance, '%s_id' % name):
                assert owner.pk == getattr(instance, '%s_id' % name)
        instance.delete()
        return HttpResponse("%s has been deleted." % self.meta.name.capitalize())

    @staticmethod
    def options(request, **kwargs):
        return HttpResponse("Options OK")

    def get_queryset(self, request, **resources):

        if self.queryset is None:
            return None

        # Make filters from URL variables or resources
        filters = dict((k, v) for k, v in resources.iteritems() if k in self.meta.model_fields)

        qs = self.queryset.filter(**filters)

        # Make filters from GET variables
        for field in request.GET.iterkeys():
            tokens = field.split(LOOKUP_SEP)
            field_name = tokens[0]

            if not field_name in self.meta.model_fields or filters.has_key(field_name):
                continue

            converter = self.model._meta.get_field(field).to_python if len(tokens) == 1 else lambda v: v
            value = map(converter, request.GET.getlist(field))

            if len(value) > 1:
                tokens.append('in')
            else:
                value = value.pop()

            try:
                qs = qs.filter(**{LOOKUP_SEP.join(tokens): value})
            except FieldError, e:
                logger.warning(e)

        return qs

    def paginate(self, request, qs):
        """ Paginate queryset.
        """
        return Paginator(request, qs, self.limit_per_page)
