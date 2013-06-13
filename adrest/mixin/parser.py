""" ADRest parse data. """
from ..utils.meta import MixinBaseMeta
from ..utils.parser import FormParser, XMLParser, JSONParser, AbstractParser
from ..utils.tools import as_tuple

__all__ = 'ParserMixin',


class ParserMeta(MixinBaseMeta):

    """ Prepare resource's parsers. """

    def __new__(mcs, name, bases, params):
        cls = super(ParserMeta, mcs).__new__(mcs, name, bases, params)

        cls._meta.parsers = as_tuple(cls._meta.parsers)
        if not cls._meta.parsers:
            raise AssertionError("Should be defined at least one parser.")

        cls._meta.default_parser = cls._meta.parsers[0]
        cls._meta.parsers_dict = dict()

        for p in cls._meta.parsers:
            if not issubclass(p, AbstractParser):
                raise AssertionError(
                    "Parser must be subclass of AbstractParser.")

            cls._meta.parsers_dict[p.media_type] = p

        return cls


class ParserMixin(object):

    """ Parse user data. """

    __metaclass__ = ParserMeta

    class Meta:
        parsers = FormParser, XMLParser, JSONParser

    def parse(self, request):
        """ Parse request content.

        :return dict: parsed data.

        """
        if request.method in ('POST', 'PUT', 'PATCH'):
            content_type = self.determine_content(request)
            if content_type:
                split = content_type.split(';', 1)
                if len(split) > 1:
                    content_type = split[0]
                content_type = content_type.strip()

            parser = self._meta.parsers_dict.get(
                content_type, self._meta.default_parser)
            data = parser(self).parse(request)
            return dict() if isinstance(data, basestring) else data
        return dict()

    @staticmethod
    def determine_content(request):
        """ Determine request content.

        :return str: request content type

        """

        if not request.META.get('CONTENT_LENGTH', None) \
           and not request.META.get('TRANSFER_ENCODING', None):
            return None

        return request.META.get('CONTENT_TYPE', None)
