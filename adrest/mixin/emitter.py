import mimeparse
from django.http import HttpResponse

from ..utils import MetaOptions
from ..utils.emitter import JSONEmitter, BaseEmitter
from ..utils.paginator import Paginator
from ..utils.tools import as_tuple


__all__ = 'EmitterMixin',


class EmitterMeta(type):
    """ Prepare resource's emiters.
    """
    def __new__(mcs, name, bases, params):
        params['meta'] = params.get('meta', MetaOptions())
        cls = super(EmitterMeta, mcs).__new__(mcs, name, bases, params)

        cls.emitters = as_tuple(cls.emitters)
        assert cls.emitters, "Resource should have emitters."
        cls.meta.emitters_dict = dict(
            (e.media_type, e) for e in cls.emitters
        )

        for e in cls.emitters:
            assert issubclass(e, BaseEmitter), \
                "Emitter should be subclass of `adrest.utils.emitter.BaseEmitter`" # nolint

        return cls


class EmitterMixin(object):
    """ Serialize response.

        :param emitters: Emitter's choosen by http header
        :param emit_template: Force template name for template based emitters
        :param emit_fields: Manualy defined set of model fields for serializers
        :param emit_include: Additionaly fields for model serialization
        :param emit_exclude: Exclude fields from model serialization
        :param emit_related: Dict with field serialization options

        Example: ::

            class SomeResource():
                emit_fields = ['pk', 'user', 'customfield']
                emit_related = {
                    'user': {
                        _fields: ['username']
                    }
                }

                def dehydrate__customfield(self, user):
                    return "I'm hero! " + user.username

    """
    __metaclass__ = EmitterMeta

    emitters = JSONEmitter
    emit_template = None
    emit_fields = None
    emit_related = None
    emit_include = None
    emit_exclude = None

    def emit(self, content, request=None, emitter=None):
        """ Serialize response.
        """
        # Get emitter for request
        emitter = emitter or self.determine_emitter(request)
        emitter = emitter(self, request=request, response=content)

        # Serialize the response content
        response = emitter.emit()
        assert isinstance(response, HttpResponse), \
            "Emitter must return HttpResponse"

        # Append pagination headers
        if isinstance(content, Paginator):
            linked_resources = []
            if content.next:
                linked_resources.append('<%s>; rel="next"' % content.next)
            if content.previous:
                linked_resources.append(
                    '<%s>; rel="previous"' % content.previous)
            response["Link"] = ", ".join(linked_resources)

        return response

    @staticmethod
    def to_simple(content, simple, serializer=None):
        """ Modify simple structure before response.
        """
        return simple

    @classmethod
    def determine_emitter(cls, request):
        " Return must fine emitter for request "
        default_emitter = cls.emitters[0]
        if not request:
            return default_emitter

        if request.method == 'OPTIONS':
            return JSONEmitter

        accept = request.META.get('HTTP_ACCEPT', '*/*')
        if accept == '*/*':
            return default_emitter

        base_format = mimeparse.best_match(cls.meta.emitters_dict.keys(),
                                           accept)
        return cls.meta.emitters_dict.get(
            base_format,
            default_emitter)
