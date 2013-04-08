from urllib import urlencode

from django.core.paginator import InvalidPage, Paginator as DjangoPaginator

from .exceptions import HttpError
from .status import HTTP_400_BAD_REQUEST


class Paginator(object):
    """ Paginate collections.
    """
    def __init__(self, request, qs, max_res):
        self.query_dict = dict(request.GET.items())
        self._page = None
        self.path = request.path

        try:
            self.paginator = DjangoPaginator(
                qs, self.query_dict.get('max') or max_res)
            assert self.paginator.per_page
        except (ValueError, AssertionError):
            self.paginator = None

    @property
    def page(self):
        if not self._page:
            try:
                self._page = self.paginator.page(
                    self.query_dict.get('page', 1))
            except InvalidPage:
                raise HttpError("Invalid page", status=HTTP_400_BAD_REQUEST)
        return self._page

    @property
    def count(self):
        return self.paginator.count

    @property
    def resources(self):
        return self.page.object_list

    @property
    def next_page(self):
        if self.page.has_next():
            self.query_dict['page'] = self.page.next_page_number()
            return "%s?%s" % (self.path, urlencode(self.query_dict))
        return ""

    @property
    def previous_page(self):
        if self.page.has_previous():
            previous = self.page.previous_page_number()
            if previous == 1:
                if 'page' in self.query_dict:
                    del self.query_dict['page']
            else:
                self.query_dict['page'] = previous
            return "%s?%s" % (self.path, urlencode(self.query_dict))
        return ""
