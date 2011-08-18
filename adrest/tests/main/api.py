from resourses import AuthorResource, BookPrefixResource, ArticleResource, SomeOtherResource
from adrest.api import Api


api = Api(
        version = (1, 0, 0),
)

api.register(AuthorResource)
api.register(BookPrefixResource)
api.register(ArticleResource)
api.register(SomeOtherResource, urlname='test', urlregex='test/mem/$')
