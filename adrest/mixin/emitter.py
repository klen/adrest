import mimeparse
from django.http import HttpResponse

from ..utils import MetaOptions
from ..utils.emitter import JSONEmitter, BaseEmitter
from ..utils.paginator import Paginator
from ..utils.tools import as_tuple


class EmitterMeta(type):

    def __new__(mcs, name, bases, params):

        params['meta'] = params.get('meta', MetaOptions())
        cls = super(EmitterMeta, mcs).__new__(mcs, name, bases, params)
        cls.emitters = as_tuple(cls.emitters)
        cache = set()
        cls.meta.default_emitter = cls.emitters[0] if cls.emitters else None
        for e in cls.emitters:
            assert issubclass(e, BaseEmitter), "Emitter must be subclass of BaseEmitter"

            # Skip dublicates
            if e in cache:
                continue
            cache.add(e)

            cls.meta.emitters_dict[e.media_type] = e
            cls.meta.emitters_types.append(e.media_type)
        return cls


class EmitterMixin(object):

    __metaclass__ = EmitterMeta

    emitters = JSONEmitter
    template = None

    def emit(self, content, request=None, emitter=None):
        " Serialize reponse "

        # Get emitter for request
        emitter = emitter or self._determine_emitter(request)
        emitter = emitter(self, request=request, response=content)

        # Serialize the response content
        response = emitter.emit()
        assert isinstance(response, HttpResponse), "Emitter must return HttpResponse"

        # Append pagination headers
        if isinstance(content, Paginator):
            linked_resources = []
            if content.next:
                linked_resources.append('<%s>; rel="next"' % content.next)
            if content.previous:
                linked_resources.append('<%s>; rel="previous"' % content.previous)
            response["Link"] = ", ".join(linked_resources)

        return response

    def _determine_emitter(self, request):
        " Return must fine emitter for request "
        if not request:
            return self.meta.default_emitter

        if request.method == 'OPTIONS':
            return JSONEmitter

        accept = request.META.get('HTTP_ACCEPT', '*/*')
        if accept == '*/*':
            return self.meta.default_emitter

        base_format = mimeparse.best_match(self.meta.emitters_types, accept)
        return self.meta.emitters_dict.get(base_format, self.meta.default_emitter)
