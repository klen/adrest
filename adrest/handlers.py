from adrest import status
from adrest.forms import PartitialForm
from adrest.utils import HttpError, Paginator


class HandlerMixin(object):

    max_resources_per_page = 50
    parent = None
    model = None
    form = None
    form_fields = None
    prefix = ''
    uri_params = None

    def get(self, request, instance=None, **kwargs):
        assert self.model, "This auto method required in model."
        if instance:
            return instance

        filter_options = self.get_filter_options(request, **kwargs)
        q = self.model.objects.select_related().filter( **filter_options )
        return self.paginate(request, q)

    def post(self, request, **kwargs):
        assert self.model, "This auto method required in model."
        form_class = self.get_form()
        form = form_class(data=request.data, **kwargs)
        if form.is_valid():
            return form.save()
        raise HttpError(form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, instance=None, **kwargs):
        assert self.model, "This auto method required in model."
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_400_BAD_REQUEST)

        form_class = self.get_form()
        form = form_class(data=request.data, instance=instance, **kwargs)
        if form.is_valid():
            return form.save()

        raise HttpError(form.errors.as_text(), status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, instance=None, **kwargs):
        if not instance:
            raise HttpError("Bad request", status=status.HTTP_400_BAD_REQUEST)

        for name, owner in kwargs.items():
            if hasattr(instance, '%s_id' % name):
                assert owner.pk == getattr(instance, '%s_id' % name)
        instance.delete()
        return None

    @classmethod
    def get_resource_name(cls):
        if cls.model:
            return cls.model._meta.module_name
        class_name = cls.__name__
        name_bits = [bit for bit in class_name.split('Resource') if bit]
        return ''.join(name_bits).lower()

    @classmethod
    def get_urlname(cls):
        parts = []

        if cls.parent:
            parts.append(cls.parent.get_urlname())

        if cls.prefix:
            parts.append(cls.prefix)

        if cls.uri_params:
            parts += list(cls.uri_params)

        parts.append(cls.get_resource_name())
        return '-'.join(parts)

    @classmethod
    def get_urlregex(cls):

        parts = []
        parent = cls.parent
        while parent:
            parts.append(parent.get_resource_name())
            parent = parent.parent

        parts = list(reversed(parts))

        if cls.uri_params:
            parts += list(cls.uri_params)

        regex = '/'.join('%(name)s/(?P<%(name)s>[^/]+)' % dict(name = p) for p in parts)
        regex = regex + '/' if regex else ''
        regex += '%(name)s/(?:(?P<%(name)s>[^/]+)/)?$' % dict(name = cls.get_resource_name())
        if cls.prefix:
            regex = '%s/%s' % (cls.prefix, regex)
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
                    fields = self.form_fields
            return DynForm
        return self.form
