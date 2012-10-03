from .resources import AuthorResource, BookPrefixResource, ArticleResource, SomeOtherResource, CustomResource, BSONResource, CSVResource
from adrest.api import Api
from adrest.utils.auth import AnonimousAuthenticator, AccessKeyAuthenticator, UserAuthenticator
from adrest.utils.emitter import XMLTemplateEmitter, JSONEmitter, BSONEmitter
from adrest.utils.parser import BSONParser
from adrest.utils.throttle import CacheThrottle


class CustomUserAuth(UserAuthenticator):
    username_fieldname = 'nickname'


API = Api(version=(1, 0, 0), emitters=(XMLTemplateEmitter, JSONEmitter), throttle=CacheThrottle, api_prefix='main')

API.register(AuthorResource,
             authenticators=(CustomUserAuth, AnonimousAuthenticator))
API.register(BookPrefixResource)
API.register(CustomResource)
API.register(ArticleResource, authenticators=AccessKeyAuthenticator)
API.register(SomeOtherResource, url_name='test', url_regex='test/mem/$')
API.register(BSONResource, parsers=(BSONParser,), emitters=(BSONEmitter,))
API.register(CSVResource)
