import base64

from django.contrib.auth import authenticate
from django.middleware.csrf import CsrfViewMiddleware

from ..models import AccessKey


class BaseAuthenticator(object):
    " Abstract base authenticator "

    def __init__(self, resource):
        self.resource = resource
        self.identifier = ''

    def authenticate(self, request=None):
        self.identifier = self.get_identifier(request)
        return self.identifier

    def get_identifier(self, request=None):
        return self.identifier

    @staticmethod
    def test_rights(resources, request=None):
        return True

    @staticmethod
    def get_fields():
        return []


class AnonimousAuthenticator(BaseAuthenticator):
    " Anonymous access "

    @staticmethod
    def get_identifier(request):
        return request.META.get('REMOTE_ADDR', 'anonymous')


class _UserAuthenticator(BaseAuthenticator):
    " Abstract class for user authentication "

    def __init__(self, resource=None):
        super(_UserAuthenticator, self).__init__(resource)
        self.user = None

    def get_identifier(self, request=None):
        if self.user and self.user.is_active:
            self.identifier = self.user.username
        return self.identifier


class UserLoggedInAuthenticator(_UserAuthenticator):
    " Authorization by session "

    def authenticate(self, request=None):
        if getattr(request, 'user', None):
            resp = CsrfViewMiddleware().process_view(request, None, (), {})
            if resp is None:  # csrf passed
                return self.get_identifier()

        return False


class BasicAuthenticator(_UserAuthenticator):
    " HTTP Basic authentication "

    def authenticate(self, request=None):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2 and auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).split(':')
                self.user = authenticate(username=uname, password=passwd)
                return self.get_identifier(request)

        return False


class UserAuthenticator(_UserAuthenticator):
    " Authorization by login and password "

    username_fieldname = 'username'
    password_fieldname = 'password'

    def authenticate(self, request=None):
        try:
            username = request.REQUEST.get(self.username_fieldname)
            password = request.REQUEST.get(self.password_fieldname)
            self.user = request.user = authenticate(username=username, password=password)
            return self.get_identifier(request)

        except KeyError:
            return False

        return False

    @classmethod
    def get_fields(cls):
        return [(cls.username_fieldname, dict(required=True)), (cls.password_fieldname, dict(required=True))]


class AccessKeyAuthenticator(_UserAuthenticator):
    " Authorization by API key "

    def authenticate(self, request=None):
        """ Authenticate user using AccessKey from HTTP Header or GET params.
        """
        try:
            access_key = request.META.get('HTTP_AUTHORIZATION') or request.REQUEST['key']
            api_key = AccessKey.objects.get(key=access_key)
            self.user = request.user = api_key.user
            return self.get_identifier(request)

        except(KeyError, AccessKey.DoesNotExist):
            return False

        return False
