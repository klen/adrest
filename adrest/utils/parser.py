from django.http import QueryDict
from django.utils import simplejson as json

from . import status
from .exceptions import HttpError


class BaseParser(object):
    media_type = None

    def __init__(self, resource):
        self.resource = resource

    def parse(self):
        return self.resource.request.raw_post_data


class JSONParser(BaseParser):
    media_type = 'application/json'

    def parse(self):
        try:
            return json.loads(self.resource.request.raw_post_data)
        except ValueError, e:
            raise HttpError('JSON parse error - %s' % str(e), status=status.HTTP_400_BAD_REQUEST)


class XMLParser(BaseParser):
    media_type = 'application/xml'


class FormParser(BaseParser):
    media_type = 'application/x-www-form-urlencoded'

    def parse(self):
        request = self.resource.request
        source = dict(request.REQUEST.iteritems())
        if request.method == "PUT" and not source:
            # Fix django bug: request.GET, .POST are empty on PUT request
            request.method = "POST"
            del request._files
            request._load_post_and_files()
            request.method = "PUT"
            source = dict(request.POST.iteritems())
        return source

