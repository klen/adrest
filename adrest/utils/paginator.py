""" Pagination support. """

from urllib import urlencode

from django.core.paginator import InvalidPage, Paginator as DjangoPaginator

from .exceptions import HttpError
from .status import HTTP_400_BAD_REQUEST


class Paginator(object):

    """ Paginate collections. """

    def __init__(self, request, resource, response):
        self.query_dict = dict(request.GET.items())
        self.path = request.path

        try:
            per_page = resource._meta.dyn_prefix + 'max'
            self.paginator = DjangoPaginator(
                response,
                self.query_dict.get(per_page) or resource._meta.limit_per_page)

            if not self.paginator.per_page:
                self.paginator = None

        except (ValueError, AssertionError):
            self.paginator = None

        self._page = None

    def to_simple(self, serializer=None):
        """ Prepare to serialization.

        :return dict: paginator params

        """
        return dict(
            count=self.paginator.count,
            page=self.page_number,
            num_pages=self.paginator.num_pages,
            next=self.next_page,
            prev=self.previous_page,
            resources=self.resources,
        )

    @property
    def page(self):
        """ Get current page.

        :return int: page number

        """
        if not self._page:
            try:
                self._page = self.paginator.page(
                    self.query_dict.get('page', 1))
            except InvalidPage:
                raise HttpError("Invalid page", status=HTTP_400_BAD_REQUEST)
        return self._page

    @property
    def page_number(self):
        """Get page number

        :return: int

        """
        return self.page.number if self.page else 1

    @property
    def count(self):
        """ Get resources count.

        :return int: resources amount

        """
        return self.paginator.count

    @property
    def resources(self):
        """ Return list of current page resources.

        :return list:

        """
        return self.page.object_list

    @property
    def next_page(self):
        """ Return URL for next page.

        :return str:

        """
        if self.page.has_next():
            self.query_dict['page'] = self.page.next_page_number()
            return "%s?%s" % (self.path, urlencode(self.query_dict))
        return ""

    @property
    def previous_page(self):
        """ Return URL for previous page.

        :return str:

        """
        if self.page.has_previous():
            previous = self.page.previous_page_number()
            if previous == 1:
                if 'page' in self.query_dict:
                    del self.query_dict['page']
            else:
                self.query_dict['page'] = previous
            return "%s?%s" % (self.path, urlencode(self.query_dict))
        return ""
