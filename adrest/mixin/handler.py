from django.db.models import get_model, Model
from django.http import HttpResponse

from adrest.forms import PartitialForm
from adrest.settings import LIMIT_PER_PAGE
from adrest.utils import status, MetaOptions
from adrest.utils.exceptions import HttpError
from adrest.utils.paginator import Paginator


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
        form = self.form(data=request.data, **resources)
        if form.is_valid():
            return form.save()
        raise HttpError(form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, **resources):
        instance = resources.get(self.meta.name)
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_404_NOT_FOUND)

        form = self.form(data=request.data, instance=instance, **resources)
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
        return 'OK'

    def get_queryset(self, request, **resources):

        if self.queryset is None:
            return None

        # Make filters from URL variables or resources
        filters = dict((k, v) for k, v in resources.iteritems() if k in self.meta.model_fields)

        # Make filters from GET variables
        for field in request.GET.iterkeys():
            if not field in self.meta.model_fields or filters.has_key(field):
                continue
            converter = self.model._meta.get_field(field).to_python
            filters[field] = map(converter, request.GET.getlist(field))

        filters = dict(
            (k, v) if not isinstance(v, (list, tuple))
            else ("%s__in" % k, v) if len(v) > 1
            else (k, v[0])
            for k, v in filters.iteritems()
        )

        return self.queryset.filter(**filters)

    def paginate(self, request, qs):
        """ Paginate queryset.
        """
        return Paginator(request, qs, self.limit_per_page)
