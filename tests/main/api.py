from adrest.api import Api
from adrest.utils.auth import AnonimousAuthenticator, AccessKeyAuthenticator, UserAuthenticator
from adrest.utils.emitter import XMLTemplateEmitter, JSONEmitter
from .resourses import AuthorResource, BookPrefixResource, ArticleResource, SomeOtherResource, CustomResource


class CustomUserAuth(UserAuthenticator):
    username_fieldname = 'nickname'


api = Api(version=(1, 0, 0), emitters=(XMLTemplateEmitter, JSONEmitter))

api.register(AuthorResource, authenticators=(AnonimousAuthenticator, CustomUserAuth))
api.register(BookPrefixResource)
api.register(ArticleResource, authenticators=AccessKeyAuthenticator)
api.register(CustomResource)
api.register(SomeOtherResource, urlname='test', urlregex='test/mem/$')

