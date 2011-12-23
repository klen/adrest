from .models import Book
from adrest.views import ResourceView


class AuthorResource(ResourceView):
    allowed_methods = 'GET', 'POST'
    model = 'main.author'


class BookResource(ResourceView):
    allowed_methods = 'GET', 'POST', 'PUT'
    model = 'main.book'
    parent = AuthorResource


class BookPrefixResource(BookResource):
    prefix = 'test'


class ArticleResource(ResourceView):
    model = 'main.article'
    parent = BookPrefixResource


class SomeOtherResource(ResourceView):
    parent = AuthorResource
    uri_params = 'device',


class CustomResource(ResourceView):
    model = 'main.book'
    queryset = Book.objects.all()
    template = 'api/custom.xml'

    def get(self, request, **kwargs):
        return list(self.queryset)
