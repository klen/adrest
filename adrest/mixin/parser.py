from adrest.utils.parser import FormParser, XMLParser, JSONParser, BaseParser
from adrest.utils import MetaOptions
from adrest.utils.tools import as_tuple


class ParserMeta(type):

    def __new__(mcs, name, bases, params):
        params['meta'] = params.get('meta', MetaOptions())
        cls = super(ParserMeta, mcs).__new__(mcs, name, bases, params)
        cls.parsers = as_tuple(cls.parsers)
        cls.meta.default_parser = cls.parsers[0] if cls.parsers else None

        for p in cls.parsers:
            assert issubclass(p, BaseParser), "Parser must be subclass of BaseParser"
            cls.meta.parsers_dict[p.media_type] = p

        return cls


class ParserMixin(object):

    __metaclass__ = ParserMeta

    parsers = FormParser, XMLParser, JSONParser

    def parse(self, request):
        " Parse request content "

        content_type = self.determine_content(request)
        if content_type:
            split = content_type.split(';', 1)
            if len(split) > 1:
                content_type = split[0]
            content_type = content_type.strip()

        parser = self.meta.parsers_dict.get(content_type, self.meta.default_parser)
        return parser(self).parse(request)

    @staticmethod
    def determine_content(request):
        " Determine request content "

        if not request.META.get('CONTENT_LENGTH', None) and not request.META.get('TRANSFER_ENCODING', None):
            return None

        return request.META.get('CONTENT_TYPE', None)
