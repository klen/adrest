from django.http import HttpResponse
from .status import HTTP_200_OK


class SerializedMeta(type):

    def __call__(mcs, content='', mimetype=None, status=None,
                 content_type=None, finaly=False, error=False):
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
            finaly=finaly,
            error=error,
        )


class SerializedHttpResponse(HttpResponse):
    """ Response has will be serialized.
        Django http response will be returned as is.

        :param finaly: Prevent serialization.
        :param error: Force error in response.
    """

    __metaclass__ = SerializedMeta

    def __init__(self, content='', mimetype=None, status=None,
                 content_type=None, finaly=False, error=False):
        """
            Save original response.
        """
        self.response = content
        self.finaly = finaly
        self._error = error
        super(SerializedHttpResponse, self).__init__(
            content,
            mimetype=mimetype,
            status=status,
            content_type=content_type)

    @property
    def error(self):
        return self._error or self.status_code != HTTP_200_OK

    def __repr__(self):
        return "<SerializedHttpResponse %s>" % self.status_code

# pymode:lint_ignore=E1103
