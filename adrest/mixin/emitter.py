import mimeparse
from django.http import HttpResponse

from adrest.utils.emitter import XMLTemplateEmitter, JSONEmitter
from adrest.utils.exceptions import HttpError
from adrest.utils.response import Response
from adrest.utils.tools import as_tuple


class EmitterMixin(object):

    emitters = XMLTemplateEmitter, JSONEmitter
    template = None

    def emit(self, request, response, emitter=None):
        """ Takes a Response object and returns a Django HttpResponse.
        """
        try:
            emitter = emitter or self._determine_emitter(request)

        except HttpError, e:
            emitter = self.default_emitter
            response = Response(content=e.message, status=e.status)

        # Serialize the response content
        content = emitter(self).emit(response=response)

        # Build the HTTP Response
        result = HttpResponse(content, mimetype=emitter.media_type, status=response.status)
        for key, val in response.headers.iteritems():
            result[key] = val

        return result

    @property
    def emitted_media_types(self):
        """ Return an list of all the media types that this resource can emit.
        """
        return [emitter.media_type for emitter in self.emitters]

    @property
    def default_emitter(self):
        """ Return the resource's most prefered emitter.
            (This emitter is used if the client does not send and Accept: header, or sends Accept: */*)
        """
        return as_tuple(self.emitters)[0]

    def _determine_emitter(self, request):
        """ Simple return first emmiter.
        """
        emiters_dict = dict((e.media_type, e) for e in as_tuple(self.emitters))
        types = emiters_dict.keys()
        accept = request.META.get('HTTP_ACCEPT', '*/*')
        if accept != '*/*':
            base_format = mimeparse.best_match(types, request.META['HTTP_ACCEPT'])
            if base_format:
                return emiters_dict.get(base_format) or self.default_emitter
        return self.default_emitter
