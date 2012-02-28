from django.http import HttpResponse


class SerializedHttpResponse(HttpResponse):
    """ Response has will be serialized.
        Django http response will be returned as is.
    """

    def __init__(self, content='', *args, **kwargs):
        self.response = content
        super(SerializedHttpResponse, self).__init__(content, *args, **kwargs)
