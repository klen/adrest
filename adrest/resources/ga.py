""" Proxy request to Google Analytics. """
from pyga.requests import Tracker, Visitor, Session, Page

from ..views import ResourceView


__all__ = 'GaResource',


class GaResource(ResourceView):

    """ Google Analytics support.

    Track GA from server.

    Example: ::

        api.register(GaResource, account_id="UA-123456", domain="test")

    """

    class Meta:
        url_regex = r'^ga(?P<path>.*)$'
        domain = None
        account_id = None

    def get(self, request, path=None, **resources):
        """ Proxy request to GA. """
        tracker = Tracker(
            self._meta.account_id,
            self._meta.domain or request.META.get('SERVER_NAME'))
        visitor = Visitor()
        visitor.extract_from_server_meta(request.META)
        session = Session()
        page = Page(path)
        tracker.track_pageview(page, session, visitor)

# lint_ignore=F0401
