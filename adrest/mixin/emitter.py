""" ADRest serialization support. """
import mimeparse
from django.http import HttpResponse

from ..utils.emitter import JSONEmitter, BaseEmitter
from ..utils.meta import MixinBaseMeta
from ..utils.paginator import Paginator
from ..utils.tools import as_tuple


__all__ = 'EmitterMixin',


class Meta:

    """ Emitter options. Setup parameters for resource's serialization.

    ::

        class SomeResource(EmitterMixin, View):

            class Meta:
                emitters = JSONEmitter

    """

    #: :class:`adrest.utils.Emitter` (or collection of them)
    #: Defined available emitters for resource.
    #: ::
    #:
    #:     class SomeResource(EmitterMixin, View):
    #:         class Meta:
    #:             emitters = JSONEmitter, XMLEmitter
    #:
    emitters = JSONEmitter

    #: Options for low-level serialization
    #: Example for JSON serialization
    #:
    #: ::
    #:
    #:     class SomeResource(EmitterMixin, View):
    #:         class Meta:
    #:             emit_options = dict(indent=2, sort_keys=True)
    #:
    emit_options = None

    #: Dictionary with emitter's options for relations
    #:
    #: * emit_models['fields'] -- Set serialized fields by manual
    #: * emit_models['exclude'] -- Exclude some fields
    #: * emit_models['include'] -- Include some fields
    #: * emit_models['related'] -- Options for relations.
    #:
    #: Example: ::
    #:
    #:     class SomeResource(EmitterMixin, View):
    #:         class Meta:
    #:             model = Role
    #:             emit_models = dict(
    #:                  include = 'group_count',
    #:                  exclude = ['password', 'service'],
    #:                  related = dict(
    #:                      user = dict(
    #:                          fields = 'username'
    #:                      )
    #:                  )
    #:
    #:              )

    #: You can use a shortcuts for `emit_models` option, as is `emit_fields` or
    #: `emit_include`. That same as bellow::
    #:
    #:     class SomeResource(EmitterMixin, View):
    #:         class Meta:
    #:             model = Role
    #:             emit_include = 'group_count'
    #:             emit_exclude = 'password', 'service'
    #:             emit_related = dict(
    #:                 user = dict(
    #:                         fields = 'username'
    #:                 )
    #:             )
    emit_models = None

    #: Define template for template-based emitters by manualy
    #: Otherwise template name will be generated from resource name
    #: (or resource.Meta.model)
    emit_template = None

    #: Serialization format. Set 'django' for django like view:

    #: ::
    #:
    #:     {
    #:         'pk': ...,
    #:         'model': ...,
    #:         'fields': {
    #:             'name': ...,
    #:             ...
    #:         }
    #:     }
    #:
    #: Or set 'simple' for simpliest serialization:
    #: ::
    #:
    #:     {
    #:         'id': ...,
    #:         'name': ...,
    #:     }
    #:
    emit_format = 'django'


class EmitterMeta(MixinBaseMeta):

    """ Prepare resource's emiters. """

    def __new__(mcs, name, bases, params):
        cls = super(EmitterMeta, mcs).__new__(mcs, name, bases, params)

        cls._meta.emitters = as_tuple(cls._meta.emitters)
        cls._meta.emitters_dict = dict(
            (e.media_type, e) for e in cls._meta.emitters
        )
        if not cls._meta.emitters:
            raise AssertionError("Should be defined at least one emitter.")

        for e in cls._meta.emitters:
            if not issubclass(e, BaseEmitter):
                raise AssertionError(
                    "Emitter should be subclass of "
                    "`adrest.utils.emitter.BaseEmitter`"
                )

        if cls._meta.emit_models is None:
            cls._meta.emit_models = dict()

        if cls._meta.emit_include:
            cls._meta.emit_models['include'] = cls._meta.emit_include

        if cls._meta.emit_exclude:
            cls._meta.emit_models['exclude'] = cls._meta.emit_exclude

        if cls._meta.emit_fields:
            cls._meta.emit_models['fields'] = cls._meta.emit_fields

        if cls._meta.emit_related:
            cls._meta.emit_models['related'] = cls._meta.emit_related

        return cls


class EmitterMixin(object):

    """ Serialize response.

    .. autoclass:: adrest.mixin.emitter.Meta
       :members:

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

    # Set default options
    Meta = Meta

    def emit(self, content, request=None, emitter=None):
        """ Serialize response.

        :return response: Instance of django.http.Response

        """
        # Get emitter for request
        emitter = emitter or self.determine_emitter(request)
        emitter = emitter(self, request=request, response=content)

        # Serialize the response content
        response = emitter.emit()

        if not isinstance(response, HttpResponse):
            raise AssertionError("Emitter must return HttpResponse")

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

        :param content: response from called method
        :param simple: structure is prepared to serialization
        :param serializer: current serializer

        :return object: structure for serialization

        ::

            class SomeResource(ResourceView):
                def get(self, request, **resources):
                    return dict(true=False)

                def to_simple(self, content, simple, serializer):
                    simple['true'] = True
                    return simple

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
