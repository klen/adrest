from .models import Book
from adrest.views import ResourceView


class AuthorResource(ResourceView):
    allowed_methods = 'GET', 'POST'
    model = 'main.author'
    url_regex = '^owner/$'


class BookResource(ResourceView):
    allowed_methods = 'GET', 'POST', 'PUT', 'DELETE'
    model = 'main.book'
    parent = AuthorResource


class BookPrefixResource(BookResource):
    prefix = 'test'


class ArticleResource(ResourceView):
    allowed_methods = 'GET', 'PUT', 'DELETE'
    model = 'main.article'
    parent = BookPrefixResource

    def put(self, request, **kwargs):
        assert False, "Assertion error"

    def delete(self, request, **kwargs):
        raise Exception("Some error")


class SomeOtherResource(ResourceView):
    parent = AuthorResource
    url_params = 'device',

    def get(self, request, **kwargs):
        return True


class CustomResource(ResourceView):
    model = 'main.book'
    queryset = Book.objects.all()
    template = 'main/custom.xml'

    def get(self, request, **kwargs):
        return list(self.queryset)
