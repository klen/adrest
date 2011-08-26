from django.core.handlers.wsgi import STATUS_CODE_TEXT

from . import status as http_status


class Response(object):
    """ Not emmited response.
    """
    def __init__(self, content, status=http_status.HTTP_200_OK, headers=None):
        self.status = status
        self.content = content
        self.headers = headers or dict()

    @property
    def status_text(self):
        """ Return reason text corrosponding to our HTTP response status code.
            Provided for convienience.
        """
        return STATUS_CODE_TEXT.get(self.status, '')
