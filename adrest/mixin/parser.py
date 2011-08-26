from adrest.utils.parser import FormParser, XMLParser, JSONParser


class ParserMixin(object):

    parsers = FormParser, XMLParser, JSONParser

    def parse(self):

        content_type = self.determine_content(self.request)
        if content_type:
            split = content_type.split(';', 1)
            if len(split) > 1:
                content_type = split[0]
            content_type = content_type.strip()

        media_type_to_parser = dict([(parser.media_type, parser) for parser in self.parsers])

        try:
            parser = media_type_to_parser[content_type]
        except KeyError:
            parser = FormParser

        return parser(self).parse()

    @staticmethod
    def determine_content(request):
        if not request.META.get('CONTENT_LENGTH', None) and not request.META.get('TRANSFER_ENCODING', None):
            return None
        return request.META.get('CONTENT_TYPE', None)
