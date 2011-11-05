from datetime import datetime
from time import mktime

from django.template import RequestContext, loader

from .paginator import Paginator
from .serializer import json_dumps, xml_dumps


class BaseEmitter(object):

    media_type = None

    def __init__(self, resource):
        self.resource = resource


class TemplateEmitter(BaseEmitter):
    """ All emitters must extend this class, set the media_type attribute, and
        override the emit() function.
    """
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
            template_name = self.get_template_dir() + self.resource.meta.name

        template_name += '.%s' % self.media_type.split('/')[-1]
        return template_name


class JSONTemplateEmitter(TemplateEmitter):
    """ Emitter which serializes to JSON.
    """
    media_type = 'application/json'


class HTMLTemplateEmitter(TemplateEmitter):
    """ HTML content.
    """
    media_type = 'text/html'


class XMLTemplateEmitter(TemplateEmitter):
    """ Emitter which serializes to XML.
    """
    media_type = 'application/xml'

    def emit(self, response):
        output = super(XMLTemplateEmitter, self).emit(response)
        ts = int(mktime(datetime.now().timetuple()))
        success = 'true' if response.status == 200 else 'false'
        return '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>' % ( success, self.resource.version, ts, output )


class JSONEmitter(BaseEmitter):

    media_type = 'application/json'

    @staticmethod
    def emit(response):
        return json_dumps(response.content)


class XMLEmitter(BaseEmitter):

    media_type = 'application/xml'

    @staticmethod
    def emit(response):
        return xml_dumps(response.content)
