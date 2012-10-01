import abc
import collections
import numbers
from datetime import datetime, date, time
from decimal import Decimal

from django.db.models import Model
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.encoding import smart_unicode

from .paginator import Paginator
from .tools import as_tuple


class AbstractSerializer(object):

    __meta__ = abc.ABCMeta

    def __init__(self, **options):
        self.options = self.init_options(**options)

    @staticmethod
    def init_options(_fields=None, _include=None, _exclude=None, **related):
        options = dict(
            _fields=set(_fields and as_tuple(_fields) or []),
            _include=set(_include and as_tuple(_include) or []),
            _exclude=set(_exclude and as_tuple(_exclude) or []),
        )
        options.update(related)
        return options

    def to_simple(self, value, **options):
        " Simplify object. "

        options = options or self.options

        if isinstance(value, basestring):
            return smart_unicode(value)

        if isinstance(value, numbers.Number):
            return value

        if isinstance(value, (datetime, date, time)):
            return self.to_simple_datetime(value)

        if isinstance(value, Decimal):
            return str(value)

        if isinstance(value, dict):
            return dict((k, self.to_simple(v, **options)) for k, v in value.iteritems())

        if isinstance(value, Paginator):
            return dict(
                count=value.count,
                page=value.page.number,
                next=value.next,
                prev=value.previous,
                resources=self.to_simple(value.resources, **options)
            )

        if isinstance(value, collections.Iterable):
            return [self.to_simple(o, **options) for o in value]

        if isinstance(value, Model):
            return self.to_simple_model(value, **options)

        return smart_unicode(value)

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
            pk=smart_unicode(value._get_pk_val(), strings_only=True),
            fields=dict(),
        )

        default_fields = set([field.name for field in value._meta.fields + value._meta.many_to_many if field.serialize])
        serialized_fields = (default_fields | options['_include']) - options['_exclude']
        for fname in options['_fields'] or serialized_fields:

            if options.get(fname):
                result['fields'][fname] = self.to_simple(
                    getattr(value, fname),
                    **self.init_options(**options.get(fname)))
                continue

            if fname in default_fields:
                field = value._meta.get_field(fname)
                result['fields'][fname] = self.to_simple(field.value_from_object(value))
                continue

            result['fields'][fname] = self.to_simple(getattr(value, fname, None))

        return result

    @abc.abstractmethod
    def serialize(self, value):
        raise NotImplementedError


class BaseSerializer(AbstractSerializer):

    def serialize(self, value):

        if isinstance(value, HttpResponse):
            return value.content

        return self.to_simple(value)


class JSONSerializer(BaseSerializer):

    def serialize(self, value):

        if isinstance(value, HttpResponse):
            return value.content

        return simplejson.dumps(self.to_simple(value))


class XMLSerializer(BaseSerializer):

    def serialize(self, value):

        if isinstance(value, HttpResponse):
            return value.content

        return ''.join(s for s in self._dumps(self.to_simple(value)))

    def _dumps(self, value):
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


# lint_ignore=W901,R0911
