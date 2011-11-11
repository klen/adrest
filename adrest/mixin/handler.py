from adrest.forms import PartitialForm
from adrest.settings import LIMIT_PER_PAGE
from adrest.utils import status
from adrest.utils.exceptions import HttpError
from adrest.utils.paginator import Paginator


class HandlerMixin(object):
    limit_per_page = LIMIT_PER_PAGE
    parent = None
    model = None
    queryset = None
    form = None
    form_fields = None
    form_exclude = None
    prefix = ''
    uri_params = None
    callmap = { 'GET': 'get', 'POST': 'post',
                'PUT': 'put', 'DELETE': 'delete', 'OPTIONS': 'options' }

    def __init__(self, *args, **kwargs):
        self.queryset = self.queryset.all() if not self.queryset is None else (
            self.model.objects.all() if self.model else None
        )
        super(HandlerMixin, self).__init__(*args, **kwargs)

    def get(self, request, instance=None, **kwargs):
        assert self.model, "This auto method required in model."
        if instance:
            return instance

        filter_options = self.get_filter_options(request, **kwargs)
        return self.paginate(request, self.queryset.filter(**filter_options))

    def post(self, request, **kwargs):
        form_class = self.get_form()
        form = form_class(data=request.data, **kwargs)
        if form.is_valid():
            return form.save()
        raise HttpError(form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, instance=None, **kwargs):
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_404_NOT_FOUND)

        form_class = self.get_form()
        form = form_class(data=request.data, instance=instance, **kwargs)
        if form.is_valid():
            return form.save()

        raise HttpError(form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def delete(request, instance=None, **kwargs):
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_400_BAD_REQUEST)

        for name, owner in kwargs.items():
            if hasattr(instance, '%s_id' % name):
                assert owner.pk == getattr(instance, '%s_id' % name)
        instance.delete()
        return None

    @staticmethod
    def options(request, **kwargs):
        return 'OK'

    def get_filter_options(self, request, **kwargs):
        model_fields = set(f.name for f in self.model._meta.fields)

        # Make filters from URL variables or params
        filter_options = dict((k, v) for k, v in kwargs.items() if k in model_fields)

        # Make filters from GET variables
        for field in request.GET.iterkeys():
            if not field in model_fields or filter_options.has_key(field):
                continue
            converter = self.model._meta.get_field(field).to_python
            filter_options[field] = map(converter, request.GET.getlist(field))

        return dict(
            (k, v) if not isinstance(v, (list, tuple))
            else ("%s__in" % k, v) if len(v) > 1
            else (k, v[0])
            for k, v in filter_options.iteritems()
        )

    def paginate(self, request, qs):
        """ Paginate queryset.
        """
        return Paginator(request, qs, self.limit_per_page)

    @classmethod
    def get_form(cls):
        if cls.model and not cls.form:
            class DynForm(PartitialForm):
                class Meta():
                    model = cls.model
                    fields = cls.form_fields
                    exclude = cls.form_exclude
            return DynForm
        return cls.form
