from django.http import HttpResponse


class SerializedMeta(type):

    def __call__(mcs, content='', mimetype=None, status=None,
                 content_type=None, finaly=False):
        """ Don't create clones.
        """

        if isinstance(content, mcs):
            return content

        if isinstance(content, HttpResponse):
            content.finaly = True
            return content

        return super(SerializedMeta, mcs).__call__(
            content,
            mimetype=mimetype,
            status=status,
            content_type=content_type,
            finaly=finaly
        )


class SerializedHttpResponse(HttpResponse):
    """ Response has will be serialized.
        Django http response will be returned as is.

        :param finaly: Prevent serialization.
    """

    __metaclass__ = SerializedMeta

    def __init__(self, content='', mimetype=None, status=None,
                 content_type=None, finaly=False):
        """
            Save original response.
        """
        self.response = content
        self.finaly = finaly
        super(SerializedHttpResponse, self).__init__(
            content,
            mimetype=mimetype,
            status=status,
            content_type=content_type)

    def __repr__(self):
        return "<SerializedHttpResponse %s>" % self.status_code
