from datetime import datetime
from time import mktime

from django.template import RequestContext, loader
from django.http import HttpResponse

from .paginator import Paginator
from .serializer import json_dumps, xml_dumps
from adrest.utils.status import HTTP_200_OK


class BaseEmitter(object):

    media_type = None

    def __init__(self, resource):
        self.resource = resource

    def emit(self, content, request=None):

        if not isinstance(content, HttpResponse):
            return HttpResponse(
                    self.serialize(content, request=request),
                    mimetype=self.media_type,
                    status=HTTP_200_OK)

        response = content
        response.content = self.serialize(response.content, response=response, request=request)
        return response

    @staticmethod
    def serialize(content, response=None, request=None):
        return content


class TemplateEmitter(BaseEmitter):
    """ All emitters must extend this class, set the media_type attribute, and
        override the emit() function.
    """
    def serialize(self, content, response=None, request=None):
        if getattr(response, 'status_code', HTTP_200_OK) == HTTP_200_OK:
            template = loader.get_template(self.get_template(content))
            content = template.render(RequestContext(request, dict(
                    content = content,
                    emitter = self,
                    resource = self.resource,
                )))
        return content

    def get_template_dir(self):
        path = 'api/%s/' % (getattr(self.resource, 'version', ''))
        model = getattr(self.resource, 'model', None)
        if model:
            path += model._meta.app_label + '/'
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

    def serialize(self, content, response=None, request=None):
        content = super(XMLTemplateEmitter, self).serialize(content, response=response, request=request)
        success = 'true' if getattr(response, 'status_code', HTTP_200_OK) == HTTP_200_OK else 'false'
        ts = int(mktime(datetime.now().timetuple()))
        return '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>' % (success, self.resource.version, ts, content)


class JSONEmitter(BaseEmitter):

    media_type = 'application/json'

    @staticmethod
    def serialize(content, **kwargs):
        return json_dumps(content)


class XMLEmitter(BaseEmitter):

    media_type = 'application/xml'

    @staticmethod
    def serialize(content, **kwargs):
        return xml_dumps(content)
