from django.http import HttpResponse
from django.template import RequestContext, loader

from adrest import status
from adrest.utils import HttpError, Paginator, Response


class EmitterMixin(object):

    emitters = tuple()

    def emit(self, response):
        """ Takes a :class:`Response` object and returns a Django :class:`HttpResponse`.
        """
        try:
            emitter = self._determine_emitter(self.request)

        except HttpError, e:
            emitter = self.default_emitter
            response = Response(content=e.message, status=e.status)

        # Serialize the response content
        content = emitter(self).emit(response=response)

        # Build the HTTP Response
        resp = HttpResponse(content, mimetype=emitter.media_type, status=response.status)
        for (key, val) in response.headers.items():
            resp[key] = val

        return resp

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
        return self.emitters[0]

    def _determine_emitter(self, request):
        """ Simple return first emmiter.
        """
        for emitter in self.emitters:
            return emitter
        raise HttpError('Could not statisfy the client\'s Accept header', status=status.HTTP_406_NOT_ACCEPTABLE)


class TemplateEmmiter(object):
    """ All emitters must extend this class, set the media_type attribute, and
        override the emit() function.
    """
    media_type = None

    def __init__(self, resource):
        self.resource = resource

    def emit(self, response):
        if response.content is None:
            return ''
        if response.status == 200:
            context = RequestContext(self.resource.request, dict(
                content = response.content,
                emitter = self,
                resource = self.resource))
            template = loader.get_template(self.get_template(response.content))
            return template.render(context)
        return response.content

    def get_template(self, content=None):
        if self.resource.handler.template:
            return self.resource.handler.template

        template_name = 'api/'
        if isinstance(content, Paginator):
            template_name += 'paginator'
        else:
            template_name = '%s%s/' % (template_name, self.resource.version) if self.resource.version else template_name
            if self.resource.handler.model:
                template_name += '%s/%s' % (self.resource.handler.model._meta.app_label, self.resource.handler.resource_name)
            else:
                template_name += self.resource.handler.resource_name
        template_name += '.%s' % self.media_type.split('/')[-1]
        return template_name


class JSONTemplateEmitter(TemplateEmmiter):
    """ Emitter which serializes to JSON.
    """
    media_type = 'application/json'


class XMLTemplateEmitter(TemplateEmmiter):
    """ Emitter which serializes to XML.
    """
    media_type = 'application/xml'

    def emit(self, response):
        output = super(XMLTemplateEmitter, self).emit(response)
        success = 'true' if response.status == 200 else 'false'
        return '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s">%s</response>' % ( success, self.resource.version, output )
