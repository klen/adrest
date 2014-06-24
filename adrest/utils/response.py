from django.http import HttpResponse

from .status import HTTP_200_OK


class SerializedMeta(type):

    def __call__(cls, content, *args, **kwargs):
        """ Don't create clones.
        """
        if isinstance(content, HttpResponse):
            return content

        return super(SerializedMeta, cls).__call__(
            content, *args, **kwargs
        )


class SerializedHttpResponse(HttpResponse): # nolint
    """ Response has will be serialized.
        Django http response will be returned as is.

        :param error: Force error in response.
    """
    __metaclass__ = SerializedMeta

    def __init__(self, content='', status=None,
                 content_type=None, error=False):
        """
            Save original response.
        """
        self.response = content
        self._error = error
        self._content_type = content_type

        super(SerializedHttpResponse, self).__init__(
            content,
            status=status,
            content_type=content_type)

    @property
    def error(self):
        return self._error or self.status_code != HTTP_200_OK

    def __repr__(self):
        return "<SerializedHttpResponse %s>" % self.status_code

# pymode:lint_ignore=E1103
