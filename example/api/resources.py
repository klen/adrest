from adrest.views import ResourceView


class AuthorResource(ResourceView):
    class Meta:
        model = 'main.author'


class BookResource(ResourceView):
    class Meta:
        allowed_methods = 'get', 'post', 'put'
        model = 'main.book'
        parent = AuthorResource

# lint_ignore=C0110
