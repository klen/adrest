from adrest import status
from adrest.forms import PartitialForm
from adrest.utils import HttpError, Paginator


class Handler(object):

    allowed_methods = ('GET', )
    max_resources_per_page = 50
    parent = None
    model = None
    form = None
    template = None
    prefix = None

    def __init__(self, **initkwargs):
        for key, value in initkwargs.iteritems():
            setattr(self, key, value)

    def get(self, request, instance=None, **kwargs):

        if instance:
            return instance

        filter_options = self.get_filter_options(request, **kwargs)
        q = self.model.objects.select_related().filter( **filter_options )
        return self.paginate(request, q)

    def post(self, request, **kwargs):

        if not self.model:
            self.not_implemented('POST')

        form_class = self.get_form()
        form = form_class(data=request.data, **kwargs)
        if form.is_valid():
            return form.save()

        raise HttpError("Bad request", status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, instance=None, **kwargs):
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_400_BAD_REQUEST)

        form_class = self.get_form()
        form = form_class(data=request.data, **kwargs)
        if form.is_valid():
            return form.save()

        raise HttpError("Bad request", status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, instance=None, **kwargs):
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_400_BAD_REQUEST)

        for name, owner in kwargs.items():
            if hasattr(instance, '%s_id' % name):
                assert owner.pk == getattr(instance, '%s_id' % name)
        instance.delete()
        return None

    def not_implemented(self, operation):
        raise HttpError('%s operation on this resource has not been implemented' % operation, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @property
    def resource_name(self):
        return self.model._meta.module_name if self.model else self.__class__.__name__.lower()

    def get_urlname(self):
        name = ''
        if self.parent:
            name = self.parent.get_urlname() + '-'
        name += self.resource_name
        return name

    def get_urlregex(self):
        parent = self.parent
        regex = ''
        while parent:
            regex = '%s/(?P<%s>\d+)/' % (parent.resource_name, parent.resource_name) + regex
            parent = parent.parent
        regex += '%s/(?:(?P<%s>\d+)/)?$' % (self.resource_name, self.resource_name)
        return regex

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
        return Paginator(request, qs, self.max_resources_per_page)

    def get_form(self):
        if not self.form:
            class DynForm(PartitialForm):
                class Meta():
                    model = self.model
            return DynForm
        return self.form
