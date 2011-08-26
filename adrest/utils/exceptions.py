from . import status as http_status


class HttpError(Exception):
    """ Represent Http Error.
    """
    def __init__(self, message, status=http_status.HTTP_400_BAD_REQUEST):
        self.message, self.status = message, status
        super(HttpError, self).__init__(message)
