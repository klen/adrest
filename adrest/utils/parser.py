import abc
import json as js

from .exceptions import HttpError
from .status import HTTP_400_BAD_REQUEST
from .tools import FrozenDict


__all__ = 'FormParser', 'JSONParser', 'RawParser', 'XMLParser', 'AbstractParser'


class AbstractParser(object):
    " Base class for parsers. "

    media_type = None

    __meta__ = abc.ABCMeta

    def __init__(self, resource):
        self.resource = resource

    @abc.abstractmethod
    def parse(self, request):
        raise NotImplementedError


class RawParser(AbstractParser):
    " Return raw post data. "

    media_type = 'text/plain'

    @staticmethod
    def parse(request):
        return request.body


class FormParser(AbstractParser):
    " Parse user data from form data. "

    media_type = 'application/x-www-form-urlencoded'

    @staticmethod
    def parse(request):
        return FrozenDict((k, v if len(v) > 1 else v[0])
                          for k, v in request.POST.iterlists())


class JSONParser(AbstractParser):
    """ Parse user data from JSON.
        http://en.wikipedia.org/wiki/JSON
    """

    media_type = 'application/json'

    @staticmethod
    def parse(request):
        try:
            return js.loads(request.body)
        except ValueError, e:
            raise HttpError('JSON parse error - %s'.format(e),
                            status=HTTP_400_BAD_REQUEST)


class XMLParser(RawParser):
    " Parse user data from XML. "

    media_type = 'application/xml'
