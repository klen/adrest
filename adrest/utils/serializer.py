from django.core.serializers import get_serializer
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils.encoding import smart_unicode
from django.utils.functional import curry
from django.utils.simplejson import dumps, loads

from .paginator import Paginator


class JSONEncoder(DjangoJSONEncoder):

    def __init__(self, *args, **kwargs):
        self.serializer = get_serializer('json')()
        self.serializer.use_natural_keys = False
        super(JSONEncoder, self).__init__(*args, **kwargs)

    def handle_fk_field(self, o, field):
        """ Handle field, without base requests.
        """
        key = getattr(o, field.column, None)
        if not key is None:
            self.serializer._current[field.name] = key
        return key

    def default(self, o):

        if isinstance(o, set):
            return list(o)

        if isinstance(o, QuerySet):
            return list(o)

        if isinstance(o, HttpResponse):
            return o.content

        if isinstance(o, Model):
            self.serializer.start_object(o)
            for field in o._meta.local_fields:
                if field.serialize:
                    if field.rel is None:
                        self.serializer.handle_field(o, field)
                    else:
                        self.handle_fk_field(o, field)
            for field in o._meta.many_to_many:
                if field.serialize:
                    self.serializer.handle_m2m_field(o, field)
            return {
                "model"  : smart_unicode(o._meta),
                "pk"     : smart_unicode(o._get_pk_val(), strings_only=True),
                "fields" : self.serializer._current
            }

        elif isinstance(o, Paginator):
            return dict(
                count = o.count,
                page = o.page.number,
                next = o.next,
                prev = o.previous,
                resources = o.resources,
            )

        return super(JSONEncoder, self).default(o)


json_dumps = curry(dumps, cls=JSONEncoder)


def xml_dumps(o):
    simple = loads(json_dumps(o))
    return ''.join(_xml_dump(simple))

def _xml_dump(o):
    tag = it = None

    if isinstance(o, list):
        tag = 'items'
        it = iter(o)

    elif isinstance(o, dict) and o.has_key('model'):
        tag = o.get('model').split('.')[1]
        it = o.iteritems()

    elif isinstance(o, dict):
        it = o.iteritems()

    elif isinstance(o, tuple):
        tag = str(o[0])
        it = (i for i in o[1:])

    else:
        yield str(o)

    if tag:
        yield "<%s>" % tag

    if it:
        try:
            while True:
                v = next(it)
                yield ''.join(_xml_dump(v))
        except StopIteration:
            pass

    if tag:
        yield "</%s>" % tag
