from django.http import HttpResponse
from django.template import RequestContext, loader
from datetime import datetime
from time import mktime

from adrest import status
from adrest.utils import HttpError, Paginator, Response


class EmitterMixin(object):

    emitters = tuple()
    template = None

    def emit(self, response):
        """ Takes a Response object and returns a Django HttpResponse.
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

    def get_template_dir(self):
        path = 'api/%s/' % ( self.resource.version or '' )
        if self.resource.model:
            path += self.resource.model._meta.app_label + '/'
        return path

    def get_template(self, content=None):
        if self.resource.template:
            return self.resource.template

        if isinstance(content, Paginator):
            template_name = 'api/paginator'
        else:
            template_name = self.get_template_dir() + self.resource.get_resource_name()

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
        ts = int(mktime(datetime.now().timetuple()))
        success = 'true' if response.status == 200 else 'false'
        return '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>' % ( success, self.resource.version, ts, output )
