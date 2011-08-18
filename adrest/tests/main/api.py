from resourses import AuthorResource, BookResource, ArticleResource, SomeOtherResource
from adrest.api import Api


api = Api(
        version = (1, 0, 0),
)

api.register(AuthorResource)
api.register(BookResource)
api.register(ArticleResource)
api.register(SomeOtherResource, urlname='test', urlregex='test/mem/$')
