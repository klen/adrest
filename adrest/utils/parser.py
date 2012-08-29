from django.utils import simplejson as json

from .exceptions import HttpError
from .status import HTTP_400_BAD_REQUEST


class BaseParser(object):
    " Base class for parsers. "

    media_type = None

    def __init__(self, resource):
        self.resource = resource

    @staticmethod
    def parse(request):
        return request.raw_post_data


class FormParser(BaseParser):
    " Parse user data from form data. "

    media_type = 'application/x-www-form-urlencoded'

    @staticmethod
    def parse(request):
        return dict(request.POST.iteritems())


class JSONParser(BaseParser):
    """ Parse user data from JSON.
        http://en.wikipedia.org/wiki/JSON
    """

    media_type = 'application/json'

    @staticmethod
    def parse(request):
        try:
            return json.loads(request.raw_post_data)
        except ValueError, e:
            raise HttpError('JSON parse error - %s' % str(e), status=HTTP_400_BAD_REQUEST)


class XMLParser(BaseParser):
    " Parse user data from XML. "

    media_type = 'application/xml'


try:
    from bson import BSON

    class BSONParser(BaseParser):
        """ Parse user data from bson.
            http://en.wikipedia.org/wiki/BSON
        """

        media_type = 'application/bson'

        @staticmethod
        def parse(request):
            try:
                return BSON(request.raw_post_data).decode()
            except ValueError, e:
                raise HttpError('BSON parse error - %s' % str(e), status=HTTP_400_BAD_REQUEST)

except ImportError:
    pass
