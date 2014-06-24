from .models import Book

from django.http import HttpResponse

from adrest.utils.emitter import JSONEmitter
from adrest.utils.exceptions import HttpError
from adrest.views import ResourceView


class AuthorResource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'POST', 'PATCH'
        model = 'main.author'
        url_regex = '^owner/$'


class BookResource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'post', 'pUt', 'DELETE'
        parent = AuthorResource
        model = 'main.book'


class BookPrefixResource(BookResource):

    class Meta:
        prefix = 'test'


class ArticleResource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'PUT', 'DELETE'
        parent = BookPrefixResource
        model = 'main.article'

    def put(self, request, **kwargs):
        assert False, "Assertion error"

    def delete(self, request, **kwargs):
        raise Exception("Some error")


class OtherResource(ResourceView):

    class Meta:
        parent = BookResource

    def get(self, request, **kwargs):
        return True


class SomeOtherResource(ResourceView):

    class Meta:
        parent = AuthorResource
        url_params = 'device',

    def get(self, request, **kwargs):
        return self.paginate(request, [1, 2, 3])


class CustomResource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'POST'
        model = 'main.book'
        queryset = Book.objects.all()
        emit_template = 'main/custom.xml'

    def get(self, request, **kwargs):
        return list(self._meta.queryset)

    def post(self, request, **resources):
        try:
            request.data['test'] = 123
        except TypeError, e:
            raise HttpError(dict(error=str(
                e)), status=400, emitter=JSONEmitter)


class DummyResource(ResourceView):

    class Meta:
        name = 'iamdummy'

    def get(self, request, **resources):
        return True


class BSONResource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'POST'

    COUNTER = 1

    def get(self, request, **resources):
        return dict(counter=self.COUNTER)

    def post(self, request, **resources):
        self.COUNTER += request.data.get('counter', 0)
        return dict(counter=self.COUNTER)


class CSVResource(ResourceView):

    class Meta:
        allowed_methods = 'GET'

    def get(self, request, **resources):
        return HttpResponse('value'.encode("utf-16"), content_type="text/csv")

# lint_ignore=C
