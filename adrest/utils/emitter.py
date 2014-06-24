""" ADRest emitters. """

from datetime import datetime
from os import path as op
from time import mktime

from django.db.models.base import ModelBase, Model
from django.template import RequestContext, loader

from ..utils import UpdatedList
from .paginator import Paginator
from .response import SerializedHttpResponse
from .serializer import JSONSerializer, XMLSerializer
from .status import HTTP_200_OK


class EmitterMeta(type):

    """ Preload format attribute. """

    def __new__(mcs, name, bases, params):
        cls = super(EmitterMeta, mcs).__new__(mcs, name, bases, params)
        if not cls.format and cls.media_type:
            cls.format = str(cls.media_type).split('/')[-1]
        return cls


class BaseEmitter(object):

    """ Base class for emitters.

    All emitters must extend this class, set the media_type attribute, and
    override the serialize() function.

    """

    __metaclass__ = EmitterMeta

    media_type = None
    format = None

    def __init__(self, resource, request=None, response=None):
        self.resource = resource
        self.request = request
        self.response = SerializedHttpResponse(
            response, content_type=self.media_type, status=HTTP_200_OK)

    def emit(self):
        """ Serialize response.

        :return response: Instance of django.http.Response

        """
        # Skip serialize
        if not isinstance(self.response, SerializedHttpResponse):
            return self.response

        self.response.content = self.serialize(self.response.response)
        self.response['Content-type'] = self.media_type
        return self.response

    @staticmethod
    def serialize(content):
        """ Low level serialization.

        :return response:

        """
        return content


class NullEmitter(BaseEmitter):

    """ Return data as is. """

    media_type = 'unknown/unknown'

    def emit(self):
        """ Do nothing.

        :return response:

        """
        return self.response


class TextEmitter(BaseEmitter):

    """ Serialize to unicode. """

    media_type = 'text/plain'

    @staticmethod
    def serialize(content):
        """ Get content and return string.

        :return unicode:

        """
        return unicode(content)


class JSONEmitter(BaseEmitter):

    """ Serialize to JSON. """

    media_type = 'application/json'

    def serialize(self, content):
        """ Serialize to JSON.

        :return string: serializaed JSON

        """
        worker = JSONSerializer(
            scheme=self.resource,
            options=self.resource._meta.emit_options,
            format=self.resource._meta.emit_format,
            **self.resource._meta.emit_models
        )
        return worker.serialize(content)


class JSONPEmitter(JSONEmitter):

    """ Serialize to JSONP. """

    media_type = 'text/javascript'

    def serialize(self, content):
        """ Serialize to JSONP.

        :return string: serializaed JSONP

        """
        content = super(JSONPEmitter, self).serialize(content)
        callback = self.request.GET.get('callback', 'callback')
        return u'%s(%s)' % (callback, content)


class XMLEmitter(BaseEmitter):

    """ Serialize to XML. """

    media_type = 'application/xml'
    xmldoc_tpl = '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>' # noqa

    def serialize(self, content):
        """ Serialize to XML.

        :return string: serialized XML

        """
        worker = XMLSerializer(
            scheme=self.resource,
            format=self.resource._meta.emit_format,
            options=self.resource._meta.emit_options,
            **self.resource._meta.emit_models
        )
        return self.xmldoc_tpl % (
            'true' if not self.response.error else 'false',
            str(self.resource.api or ''),
            int(mktime(datetime.now().timetuple())),
            worker.serialize(content)
        )


class TemplateEmitter(BaseEmitter):

    """ Serialize by django templates. """

    def serialize(self, content):
        """ Render Django template.

        :return string: rendered content

        """
        if self.response.error:
            template_name = op.join('api', 'error.%s' % self.format)
        else:
            template_name = (self.resource._meta.emit_template
                             or self.get_template_path(content))

        template = loader.get_template(template_name)

        return template.render(RequestContext(self.request, dict(
            content=content,
            emitter=self,
            resource=self.resource)))

    def get_template_path(self, content=None):
        """ Find template.

        :return string: remplate path

        """
        if isinstance(content, Paginator):
            return op.join('api', 'paginator.%s' % self.format)

        if isinstance(content, UpdatedList):
            return op.join('api', 'updated.%s' % self.format)

        app = ''
        name = self.resource._meta.name

        if not content:
            content = self.resource._meta.model

        if isinstance(content, (Model, ModelBase)):
            app = content._meta.app_label
            name = content._meta.module_name

        basedir = 'api'
        if getattr(self.resource, 'api', None):
            basedir = self.resource.api.prefix

        return op.join(
            basedir,
            str(self.resource.api or ''), app, "%s.%s" % (name, self.format)
        )


class JSONTemplateEmitter(TemplateEmitter):

    """ Template emitter with JSON media type. """

    media_type = 'application/json'


class JSONPTemplateEmitter(TemplateEmitter):

    """ Template emitter with javascript media type. """

    media_type = 'text/javascript'
    format = 'json'

    def serialize(self, content):
        """ Move rendered content to callback.

        :return string: JSONP

        """
        content = super(JSONPTemplateEmitter, self).serialize(content)
        callback = self.request.GET.get('callback', 'callback')
        return '%s(%s)' % (callback, content)


class HTMLTemplateEmitter(TemplateEmitter):

    """ Template emitter with HTML media type. """

    media_type = 'text/html'


class XMLTemplateEmitter(TemplateEmitter):

    """ Template emitter with XML media type. """

    media_type = 'application/xml'
    xmldoc_tpl = '<?xml version="1.0" encoding="utf-8"?>\n<response success="%s" version="%s" timestamp="%s">%s</response>' # noqa

    def serialize(self, content):
        """ Serialize to xml.

        :return string:

        """
        return self.xmldoc_tpl % (
            'true' if self.response.status_code == HTTP_200_OK else 'false',
            str(self.resource.api or ''),
            int(mktime(datetime.now().timetuple())),
            super(XMLTemplateEmitter, self).serialize(content)
        )


try:
    from bson import BSON  # noqa

    class BSONEmitter(BaseEmitter):

        """ Emit to bson. """

        media_type = 'application/bson'

        @staticmethod
        def serialize(content):
            return BSON.encode(content)

except ImportError:
    pass

# pymode:lint_ignore=F0401,W0704
