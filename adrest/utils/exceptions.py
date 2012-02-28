from .status import HTTP_400_BAD_REQUEST


class HttpError(Exception):
    " Represent HTTP Error. "

    def __init__(self, content, status=HTTP_400_BAD_REQUEST, emitter=None):
        self.content, self.status, self.emitter = content, status, emitter
        super(HttpError, self).__init__(content)

    def __str__(self):
        return self.content

    __repr__ = __str__
