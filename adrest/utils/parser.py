from django.utils import simplejson as json

from . import status
from .exceptions import HttpError


class BaseParser(object):

    media_type = None

    def __init__(self, resource):
        self.resource = resource

    @staticmethod
    def parse(request):
        return request.raw_post_data


class JSONParser(BaseParser):

    media_type = 'application/json'

    @staticmethod
    def parse(request):
        try:
            return json.loads(request.raw_post_data)
        except ValueError, e:
            raise HttpError('JSON parse error - %s' % str(e), status=status.HTTP_400_BAD_REQUEST)


class XMLParser(BaseParser):

    media_type = 'application/xml'


class FormParser(BaseParser):

    media_type = 'application/x-www-form-urlencoded'

    @staticmethod
    def parse(request):
        return dict(request.POST.iteritems())
