from adrest.views import ResourceView
from .models import Author, Book, Article


class AuthorResource(ResourceView):
    allowed_methods = 'GET', 'POST'
    model = Author


class BookResource(ResourceView):
    allowed_methods = 'GET', 'POST', 'PUT'
    model = Book
    parent = AuthorResource


class BookPrefixResource(BookResource):
    prefix = 'test'


class ArticleResource(ResourceView):
    model = Article
    parent = BookPrefixResource


class SomeOtherResource(ResourceView):
    parent = AuthorResource
    uri_params = 'device',


class CustomResource(ResourceView):
    model = Book
    queryset = Book.objects.all()
    template = 'api/custom.xml'

    def get(self, request, **kwargs):
        return list(self.queryset)
