from pyga.requests import Tracker, Visitor, Session, Page

from ..views import ResourceView


class GaResource(ResourceView):
    """
        Google Analytics support.
        -------------------------

        Track GA from server.

        Example: ::

            api.register(GaResource, account_id="UA-123456", domain="test")

    """

    url_regex = r'^ga(?P<path>.*)$'
    domain = None
    account_id = None

    def get(self, request, path=None, **resources):
        tracker = Tracker(
            self.account_id, self.domain or request.META.get('SERVER_NAME'))
        visitor = Visitor()
        visitor.extract_from_server_meta(request.META)
        session = Session()
        page = Page(path)
        tracker.track_pageview(page, session, visitor)
