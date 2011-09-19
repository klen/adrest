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

    def get(self, request, instance=None, **kwargs):
        assert self.model, "This auto method required in model."
        if instance:
            return instance

        filter_options = self.get_filter_options(request, **kwargs)
        query = self.queryset if not self.queryset is None else self.model.objects.all()
        return self.paginate(request, query.filter( **filter_options ))

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
        model_fields = [f.name for f in self.model._meta.fields]
        fields_converters = dict((f.name, f.to_python) for f in self.model._meta.fields )

        # Make filters from URL variables
        filter_options = dict((k, v) for k, v in kwargs.items() if k in model_fields)

        # Replace value in filters by objects (if exsits)
        filter_options.update( dict((k, v) for k, v in kwargs.items() if k in model_fields) )

        # FIXME Im realy need this?
        for filter_name, value in request.GET.items():
            field_name = filter_name.split("__")[0]
            if field_name in model_fields and not filter_options.has_key(field_name):
                filter_options[str(filter_name)] = fields_converters[field_name](value)

        return filter_options

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
