from datetime import datetime
from os import path as op
from time import mktime

from django.db.models.base import ModelBase, Model
from django.http import HttpResponse
from django.template import RequestContext, loader

from .paginator import Paginator
from .serializer import json_dumps, xml_dumps
from adrest.utils.status import HTTP_200_OK
from adrest.utils.response import SerializedHttpResponse


class EmitterMeta(type):
    " Preload format attribute. "
    def __new__(mcs, name, bases, params):
        cls = super(EmitterMeta, mcs).__new__(mcs, name, bases, params)
        if not cls.format and cls.media_type:
            cls.format = str(cls.media_type).split('/')[-1]
        return cls


class BaseEmitter(object):
    """ All emitters must extend this class, set the media_type attribute, and
        override the serialize() function.
    """
    __metaclass__ = EmitterMeta

    media_type = None
    format = None

    def __init__(self, resource, request=None, response=None):
        self.resource = resource
        self.request = request
        self.response = response
        if not isinstance(response, HttpResponse):
            self.response = SerializedHttpResponse(response, mimetype=self.media_type, status=HTTP_200_OK)

    def emit(self):
        if not isinstance(self.response, SerializedHttpResponse):
            return self.response

        self.response.content = self.serialize(self.response.response)
        return self.response

    @staticmethod
    def serialize(content):
        " Get content and return string. "
        return content


class TextEmitter(BaseEmitter):
    media_type = 'text/plain'

    @staticmethod
    def serialize(content):
        " Get content and return string. "
        return unicode(content)


class JSONEmitter(BaseEmitter):
    media_type = 'application/json'

    @staticmethod
    def serialize(content):
        return json_dumps(content)


class XMLEmitter(BaseEmitter):

    media_type = 'application/xml'
    xmldoc_tpl = '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>'

    def serialize(self, content):
        return self.xmldoc_tpl % (
            'true' if self.response.status_code == HTTP_200_OK else 'false',
            self.resource.version,
            int(mktime(datetime.now().timetuple())),
            xml_dumps(content)
        )


class TemplateEmitter(BaseEmitter):
    " Serialize by django templates. "

    def serialize(self, content):
        if self.response.status_code != HTTP_200_OK:
            template_name = op.join('api', 'error.%s' % self.format)
        else:
            template_name = self.resource.template or self.get_template_path(content)

        template = loader.get_template(template_name)
        return template.render(RequestContext(self.request, dict(
                content = content,
                emitter = self,
                resource = self.resource)))

    def get_template_path(self, content=None):

        if isinstance(content, Paginator):
            return op.join('api', 'paginator.%s' % self.format)

        app = ''
        name = self.resource.meta.name

        if not content:
            content = self.resource.model

        if isinstance(content, (Model, ModelBase)):
            app = content._meta.app_label
            name = content._meta.module_name

        basedir = self.resource.api.prefix if getattr(self.resource, 'api', None) else 'api'
        return op.join(
            basedir,
            self.resource.version,
            app,
            "%s.%s" % (name, self.format)
        )


class JSONTemplateEmitter(TemplateEmitter):
    " Template emitter with JSON media type. "
    media_type = 'application/json'


class HTMLTemplateEmitter(TemplateEmitter):
    " Template emitter with HTML media type. "
    media_type = 'text/html'


class XMLTemplateEmitter(TemplateEmitter):
    " Template emitter with XML media type. "

    media_type = 'application/xml'
    xmldoc_tpl = '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>'

    def serialize(self, content):
        return self.xmldoc_tpl % (
            'true' if self.response.status_code == HTTP_200_OK else 'false',
            self.resource.version,
            int(mktime(datetime.now().timetuple())),
            super(XMLTemplateEmitter, self).serialize(content)
        )
