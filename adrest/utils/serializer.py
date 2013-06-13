""" ADRest serializers. """
import collections
import inspect
from numbers import Number
from datetime import datetime, date, time
from decimal import Decimal

from django.db.models import Model, Manager
from django.utils import simplejson
from django.utils.encoding import smart_unicode

from .tools import as_tuple


class BaseSerializer(object):

    """ Abstract class for serializers. """

    def __init__(
            self, scheme=None, options=None, format='django', **model_options):
        self.scheme = scheme
        self.format = format
        self.serializer_options = options or dict()
        self.model_options = self.init_options(**model_options)

    @staticmethod
    def init_options(fields=None, include=None, exclude=None, related=None):
        options = dict(
            fields=set(as_tuple(fields)),
            include=set(as_tuple(include)),
            exclude=set(as_tuple(exclude)),
            related=related or dict(),
        )
        return options

    def to_simple(self, value, **options):  # nolint
        " Simplify object. "

        # (string, unicode)
        if isinstance(value, basestring):
            return smart_unicode(value)

        # (int, long, float, real, complex, decimal)
        if isinstance(value, Number):
            return float(str(value)) if isinstance(value, Decimal) else value

        # (datetime, data, time)
        if isinstance(value, (datetime, date, time)):
            return self.to_simple_datetime(value)

        # (dict, ordereddict, mutable mapping)
        if isinstance(value, collections.MutableMapping):
            return dict(
                (k, self.to_simple(v, **options)) for k, v in value.items())

        # (tuple, list, set, iterators)
        if isinstance(value, collections.Iterable):
            return [self.to_simple(o, **options) for o in value]

        # (None, True, False)
        if value is None or value is True or value is False:
            return value

        if hasattr(value, 'to_simple') and not inspect.isclass(value):
            return self.to_simple(
                value.to_simple(self),
                **options
            )

        if isinstance(value, Model):
            return self.to_simple_model(value, **options)

        return str(value)

    @staticmethod
    def to_simple_datetime(value):
        result = value.isoformat()
        if isinstance(value, datetime):
            if value.microsecond:
                result = result[:23] + result[26:]
            if result.endswith('+00:00'):
                result = result[:-6] + 'Z'
        elif isinstance(value, time) and value.microsecond:
            result = result[:12]
        return result

    def to_simple_model(self, instance, **options): # nolint
        """ Convert model to simple python structure.
        """
        options = self.init_options(**options)
        fields, include, exclude, related = options['fields'], options['include'], options['exclude'], options['related'] # nolint

        result = dict(
            model=smart_unicode(instance._meta),
            pk=smart_unicode(
                instance._get_pk_val(), strings_only=True),
            fields=dict(),
        )

        m2m_fields = [f.name for f in instance._meta.many_to_many]
        o2m_fields = [f.get_accessor_name()
                      for f in instance._meta.get_all_related_objects()]
        default_fields = set([field.name for field in instance._meta.fields
                              if field.serialize])
        serialized_fields = fields or (default_fields | include) - exclude

        for fname in serialized_fields:

            # Respect `to_simple__<fname>`
            to_simple = getattr(
                self.scheme, 'to_simple__{0}'.format(fname), None)

            if to_simple:
                result['fields'][fname] = to_simple(instance, serializer=self)
                continue

            related_options = related.get(fname, dict())
            if related_options:
                related_options = self.init_options(**related_options)

            if fname in default_fields and not related_options:
                field = instance._meta.get_field(fname)
                value = field.value_from_object(instance)

            else:
                value = getattr(instance, fname, None)
                if isinstance(value, Manager):
                    value = value.all()

            result['fields'][fname] = self.to_simple(
                value, **related_options)

        if self.format != 'django':
            fields = result['fields']
            fields['id'] = result['pk']
            result = fields

        return result

    def serialize(self, value):
        simple = self.to_simple(value, **self.model_options)
        if self.scheme:
            to_simple = getattr(self.scheme, 'to_simple', lambda s: s)
            simple = to_simple(value, simple, serializer=self)

        return simple


class JSONSerializer(BaseSerializer):

    def serialize(self, value):
        simple = super(JSONSerializer, self).serialize(value)
        return simplejson.dumps(simple, **self.serializer_options)


class XMLSerializer(BaseSerializer):

    def serialize(self, value):
        simple = super(XMLSerializer, self).serialize(value)
        return ''.join(s for s in self._dumps(simple))

    def _dumps(self, value):  # nolint
        tag = it = None

        if isinstance(value, list):
            tag = 'items'
            it = iter(value)

        elif isinstance(value, dict) and 'model' in value:
            tag = value.get('model').split('.')[1]
            it = value.iteritems()

        elif isinstance(value, dict):
            it = value.iteritems()

        elif isinstance(value, tuple):
            tag = str(value[0])
            it = (i for i in value[1:])

        else:
            yield str(value)

        if tag:
            yield "<%s>" % tag

        if it:
            try:
                while True:
                    v = next(it)
                    yield ''.join(self._dumps(v))
            except StopIteration:
                yield ''

        if tag:
            yield "</%s>" % tag


# lint_ignore=W901,R0911,W0212,W0622
