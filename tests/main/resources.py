from .models import Book

from django.http import HttpResponse

from adrest.utils.emitter import JSONEmitter
from adrest.utils.exceptions import HttpError
from adrest.views import ResourceView


class AuthorResource(ResourceView):
    allowed_methods = 'GET', 'POST', 'PATCH'
    model = 'main.author'
    url_regex = '^owner/$'


class BookResource(ResourceView):
    allowed_methods = 'GET', 'post', 'pUt', 'DELETE'
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
        try:
            request.data['test'] = 123
        except TypeError, e:
            raise HttpError(dict(error=str(e)), status=400, emitter=JSONEmitter)


class DummyResource(ResourceView):
    def get(self, request, **resources):
        return True


class BSONResource(ResourceView):

    allowed_methods = 'GET', 'POST'

    COUNTER = 1

    def get(self, request, **resources):
        return dict(counter=self.COUNTER)

    def post(self, request, **resources):
        self.COUNTER += request.data.get('counter', 0)
        return dict(counter=self.COUNTER)


class CSVResource(ResourceView):
    allowed_methods = 'GET'

    def get(self, request, **resources):
        return HttpResponse('value'.encode("utf-16"), mimetype="text/csv")
