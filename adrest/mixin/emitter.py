import mimeparse

from adrest.utils import MetaOptions
from adrest.utils.emitter import JSONEmitter, BaseEmitter
from adrest.utils.tools import as_tuple


class EmitterMeta(type):

    def __new__(mcs, name, bases, params):

        params['meta'] = params.get('meta', MetaOptions())
        cls = super(EmitterMeta, mcs).__new__(mcs, name, bases, params)
        cls.emitters = as_tuple(cls.emitters)
        cls.meta.default_emitter = cls.emitters[0] if cls.emitters else None
        for e in cls.emitters:
            assert issubclass(e, BaseEmitter), "Emitter must be subclass of BaseEmitter"
            cls.meta.emitters_dict[e.media_type] = e
            cls.meta.emitters_types.append(e.media_type)
        return cls


class EmitterMixin(object):

    __metaclass__ = EmitterMeta

    emitters = JSONEmitter
    template = None

    def emit(self, content, request=None, emitter=None):
        " Takes a Response object and returns a Django HttpResponse "

        # Get emitter for request
        emitter = emitter or self._determine_emitter(request)

        # Serialize the response content
        return emitter(self).emit(content, request=request)

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
