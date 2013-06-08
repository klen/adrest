""" ADRest serialization support. """
import mimeparse
from django.http import HttpResponse

from ..utils.meta import MetaBase
from ..utils.emitter import JSONEmitter, BaseEmitter
from ..utils.paginator import Paginator
from ..utils.tools import as_tuple


__all__ = 'EmitterMixin',


class EmitterMeta(MetaBase):

    """ Prepare resource's emiters. """

    def __new__(mcs, name, bases, params):
        cls = super(EmitterMeta, mcs).__new__(mcs, name, bases, params)

        cls._meta.emitters = as_tuple(cls._meta.emitters)
        assert cls._meta.emitters, "Resource should have emitters."
        cls._meta.emitters_dict = dict(
            (e.media_type, e) for e in cls._meta.emitters
        )

        assert cls._meta.emitters, "Should be defined at least one emitter."

        for e in cls._meta.emitters:
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
            class Meta:
                emit_fields = ['pk', 'user', 'customfield']
                emit_related = {
                    'user': {
                        fields: ['username']
                    }
                }

            def to_simple__customfield(self, user):
                return "I'm hero! " + user.username

    """

    __metaclass__ = EmitterMeta

    class Meta:
        emitters = JSONEmitter
        emit_exclude = None
        emit_fields = None
        emit_include = None
        emit_options = None
        emit_related = None
        emit_template = None

    def emit(self, content, request=None, emitter=None):
        """ Serialize response.

        :return response: Instance of django.http.Response

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
            if content.next_page:
                linked_resources.append('<{0}>; rel="next"'.format(
                    content.next_page))
            if content.previous_page:
                linked_resources.append(
                    '<{0}>; rel="previous"'.format(content.previous_page))
            response["Link"] = ", ".join(linked_resources)

        return response

    @staticmethod
    def to_simple(content, simple, serializer=None):
        """ Abstract method for modification a structure before serialization.

        :return simple: object

        """
        return simple

    @classmethod
    def determine_emitter(cls, request):
        """ Get emitter for request.

        :return emitter: Instance of adrest.utils.emitters.BaseEmitter

        """
        default_emitter = cls._meta.emitters[0]
        if not request:
            return default_emitter

        if request.method == 'OPTIONS':
            return JSONEmitter

        accept = request.META.get('HTTP_ACCEPT', '*/*')
        if accept == '*/*':
            return default_emitter

        base_format = mimeparse.best_match(cls._meta.emitters_dict.keys(),
                                           accept)
        return cls._meta.emitters_dict.get(
            base_format,
            default_emitter)
