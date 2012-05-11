from .models import Book
from adrest.utils.emitter import JSONEmitter
from adrest.utils.exceptions import HttpError
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


class OtherResource(ResourceView):
    parent = BookResource
    url_prefix = 'other'

    def get(self, request, **kwargs):
        return True


class SomeOtherResource(ResourceView):
    parent = AuthorResource
    url_params = 'device',

    def get(self, request, **kwargs):
        return self.paginate(request, [1, 2, 3])


class CustomResource(ResourceView):
    allowed_methods = 'GET', 'POST'
    model = 'main.book'
    queryset = Book.objects.all()
    template = 'main/custom.xml'

    def get(self, request, **kwargs):
        return list(self.queryset)

    def post(self, request, **resources):
        raise HttpError(dict(error=True), status=400, emitter=JSONEmitter)
