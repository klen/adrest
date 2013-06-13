""" Filters and sorting support. """
from django.core.exceptions import FieldError
from logging import getLogger

from ..settings import ADREST_LIMIT_PER_PAGE
from ..utils import UpdatedList
from ..utils.meta import MixinBaseMeta, MixinBase
from ..utils.paginator import Paginator


logger = getLogger('django.request')

# Separator used to split filter strings apart.
LOOKUP_SEP = '__'


class Meta:

    """ Options for dynamic mixin.

    Setup parameters for filtering and sorting a resources.

    ::
        class SomeResource(DynamicMixin, View):

            class Meta:
                dyn_prefix = 'dyn-'

    """

    #: Prefix for dynamic fields
    dyn_prefix = 'adr-'

    #: Limit per page for pagination
    #: Set to `0` for disable pagination in resource, but user can still force
    #: it with `?max=...`
    limit_per_page = ADREST_LIMIT_PER_PAGE

    #: Define queryset for resource's operation.
    #: By default: self.Meta.model.objects.all()
    queryset = None


class DynamicMixinMeta(MixinBaseMeta):

    """ Prepare dynamic class. """

    def __new__(mcs, name, bases, params):

        cls = super(DynamicMixinMeta, mcs).__new__(mcs, name, bases, params)

        if not cls._meta.dyn_prefix:
            raise AssertionError("Resource.Meta.dyn_prefix should be defined.")

        if cls._meta.model and cls._meta.queryset is None:
            cls._meta.queryset = cls._meta.model.objects.all()

        return cls


class DynamicMixin(MixinBase):

    """ Implement filters and sorting.

    ADRest DynamicMixin supports filtering and sorting collection from query
    params.

    """

    __metaclass__ = DynamicMixinMeta

    Meta = Meta

    def __init__(self, *args, **kwargs):
        """ Copy self queryset for prevent query caching. """

        super(DynamicMixin, self).__init__(*args, **kwargs)

        if not self._meta.queryset is None:
            self._meta.queryset = self._meta.queryset.all()

    def get_collection(self, request, **resources):
        """ Get filters and return filtered result.

        :return collection: collection of related resources.

        """

        if self._meta.queryset is None:
            return []

        # Filter collection
        filters = self.get_filters(request, **resources)
        filters.update(self.get_default_filters(**resources))
        qs = self._meta.queryset
        for key, (value, exclude) in filters.items():
            try:
                if exclude:
                    qs = qs.exclude(**{key: value})

                else:
                    qs = qs.filter(**{key: value})
            except FieldError, e:
                logger.warning(e)

        sorting = self.get_sorting(request, **resources)
        if sorting:
            qs = qs.order_by(*sorting)

        return qs

    def get_default_filters(self, **resources):
        """ Return default filters by a model fields.

        :return dict: name, field

        """
        return dict((k, (v, False)) for k, v in resources.items()
                    if k in self._meta.fields)

    def get_filters(self, request, **resources):
        """ Make filters from GET variables.

        :return dict: filters

        """
        filters = dict()

        if not self._meta.fields:
            return filters

        for field in request.GET.iterkeys():
            tokens = field.split(LOOKUP_SEP)
            field_name = tokens[0]

            if not field_name in self._meta.fields:
                continue

            exclude = False
            if tokens[-1] == 'not':
                exclude = True
                tokens.pop()

            converter = self._meta.model._meta.get_field(
                field_name).to_python if len(tokens) == 1 else lambda v: v
            value = map(converter, request.GET.getlist(field))

            if len(value) > 1:
                tokens.append('in')
            else:
                value = value.pop()

            filters[LOOKUP_SEP.join(tokens)] = (value, exclude)

        return filters

    def get_sorting(self, request, **resources):
        """ Get sorting options.

        :return list: sorting order

        """
        sorting = []

        if not request.GET:
            return sorting

        prefix = self._meta.dyn_prefix + 'sort'
        return request.GET.getlist(prefix)

    def paginate(self, request, collection):
        """ Paginate collection.

        :return object: Collection or paginator

        """
        p = Paginator(request, self, collection)
        return p.paginator and p or UpdatedList(collection)
