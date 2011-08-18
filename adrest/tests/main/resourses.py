from adrest.views import ResourceView
from models import Author, Book, Article


class AuthorResource(ResourceView):
    model = Author


class BookResource(ResourceView):
    model = Book
    parent = AuthorResource
    prefix = 'test'


class ArticleResource(ResourceView):
    model = Article
    parent = BookResource


class SomeOtherResource(ResourceView):
    parent = AuthorResource
    uri_params = 'device',
