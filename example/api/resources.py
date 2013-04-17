from adrest.views import ResourceView


class AuthorResource(ResourceView):
    model = 'main.author'


class BookResource(ResourceView):
    parent = AuthorResource
    model = 'main.book'
    allowed_methods = 'get', 'post', 'put'
