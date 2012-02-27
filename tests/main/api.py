from .resourses import AuthorResource, BookPrefixResource, ArticleResource, SomeOtherResource, CustomResource
from adrest.api import Api
from adrest.utils.auth import AnonimousAuthenticator, AccessKeyAuthenticator, UserAuthenticator
from adrest.utils.emitter import XMLTemplateEmitter, JSONEmitter


class CustomUserAuth(UserAuthenticator):
    username_fieldname = 'nickname'


API = Api(version=(1, 0, 0), emitters=(XMLTemplateEmitter, JSONEmitter), api_prefix='main')

API.register(AuthorResource,
        authenticators=(CustomUserAuth, AnonimousAuthenticator))
API.register(BookPrefixResource)
API.register(ArticleResource, authenticators=AccessKeyAuthenticator)
API.register(CustomResource)
API.register(SomeOtherResource, url_name='test', url_regex='test/mem/$')
