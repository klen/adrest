from urllib import urlencode

from django.core.handlers.wsgi import STATUS_CODE_TEXT
from django.core.paginator import InvalidPage, Paginator as DjangoPaginator

from adrest.status import HTTP_400_BAD_REQUEST, HTTP_200_OK


def as_tuple(obj):
    """Given obj return a tuple"""
    if obj is None:
        return ()
    elif isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, tuple):
        return obj
    return (obj,)


class HttpError(Exception):
    """ Represent Http Error.
    """
    def __init__(self, message, status=HTTP_400_BAD_REQUEST):
        self.message = message
        self.status = status
        super(HttpError, self).__init__(message)

    def __str__(self):
        return self.message


class Response(object):
    """ Not emmited response.
    """
    def __init__(self, content, status=HTTP_200_OK, headers=None):
        self.status = status
        self.content = content
        self.headers = headers or dict()

    @property
    def status_text(self):
        """ Return reason text corrosponding to our HTTP response status code.
            Provided for convienience.
        """
        return STATUS_CODE_TEXT.get(self.status, '')


class Paginator(object):
    """ Paginate querysets.
    """
    def __init__(self, request, qs,  max_res):
        self.query_dict = dict(request.GET.items())
        self.paginator = DjangoPaginator(qs, int(self.query_dict.get('max') or max_res))
        self.path = request.path
        self.name = qs.model._meta.module_name
        page_num = int(request.REQUEST.get('page', 1))
        try:
            self.page = self.paginator.page(page_num)
        except InvalidPage:
            raise HttpError("Invalid page", status=HTTP_400_BAD_REQUEST)

    @property
    def count(self):
        return self.paginator.count

    @property
    def resources(self):
        return self.page.object_list

    @property
    def next(self):
        if self.page.has_next():
            self.query_dict['page'] = self.page.next_page_number()
            return "%s?%s" % (self.path, urlencode(self.query_dict))
        return ""

    @property
    def previous(self):
        if self.page.has_previous():
            previous = self.page.previous_page_number()
            if previous == 1:
                if 'page' in self.query_dict:
                    del self.query_dict['page']
            else:
                self.query_dict['page'] = previous
            return "%s?%s" % (self.path, urlencode(self.query_dict))
        return ""
