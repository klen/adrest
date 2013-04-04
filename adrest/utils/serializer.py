import collections
from numbers import Number
from datetime import datetime, date, time
from decimal import Decimal

from django.db.models import Model
from django.utils import simplejson
from django.utils.encoding import smart_unicode

from .paginator import Paginator
from .tools import as_tuple


class BaseSerializer(object):

    def __init__(self, _scheme=None, **options):
        self.scheme = _scheme
        self.options = self.init_options(**options)

    @staticmethod
    def init_options(_fields=None, _include=None, _exclude=None, **related):
        options = dict(
            _fields=set(as_tuple(_fields)),
            _include=set(as_tuple(_include)),
            _exclude=set(as_tuple(_exclude)),
        )
        options.update(related)
        return options

    def to_simple(self, value, **options): # nolint
        " Simplify object. "

        options = options or self.options

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

        if isinstance(value, Paginator):
            return dict(
                count=value.count,
                page=value.page.number,
                next=value.next,
                prev=value.previous,
                resources=self.to_simple(value.resources, **options)
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

    def to_simple_model(self, value, **options):

        result = dict(
            model=smart_unicode(value._meta),
            pk=smart_unicode(
                value._get_pk_val(), strings_only=True),
            fields=dict(),
        )

        m2m_fields = [f.name for f in value._meta.many_to_many]
        o2m_fields = [f.get_accessor_name()
                      for f in value._meta.get_all_related_objects()]
        default_fields = set([field.name for field in value._meta.fields
                              if field.serialize])
        serialized_fields = (default_fields | options[
                             '_include']) - options['_exclude']
        for fname in options['_fields'] or serialized_fields:

            to_simple = getattr(self.scheme,
                                'to_simple__{0}'.format(fname),
                                None)
            if to_simple:
                result['fields'][fname] = to_simple(value)
                continue

            # Related serialization
            if options.get(fname):
                target = getattr(value, fname)
                if fname in m2m_fields + o2m_fields:
                    target = target.all()
                result['fields'][fname] = self.to_simple(
                    target, **self.init_options(**options.get(fname)))
                continue

            if fname in default_fields:
                field = value._meta.get_field(fname)
                result['fields'][fname] = self.to_simple(
                    field.value_from_object(value))
                continue

            result['fields'][fname] = self.to_simple(
                getattr(value, fname, None))

        return result

    def serialize(self, value):
        simple = self.to_simple(value)
        if self.scheme:
            to_simple = getattr(self.scheme, 'to_simple', lambda s: s)
            simple = to_simple(value, simple)

        return simple


class JSONSerializer(BaseSerializer):

    def serialize(self, value):
        simple = super(JSONSerializer, self).serialize(value)
        return simplejson.dumps(simple)


class XMLSerializer(BaseSerializer):

    def serialize(self, value):
        simple = super(XMLSerializer, self).serialize(value)
        return ''.join(s for s in self._dumps(simple))

    def _dumps(self, value): # nolint
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


# lint_ignore=W901,R0911,W0212
