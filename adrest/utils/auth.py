import abc
import base64

from django.contrib.auth import authenticate

from ..models import AccessKey


class AbstractAuthenticator(object):
    " Abstract base authenticator "

    __meta__ = abc.ABCMeta

    def __init__(self, resource):
        self.resource = resource
        self.identifier = ''

    @abc.abstractmethod
    def authenticate(self, request):
        raise NotImplementedError

    @abc.abstractmethod
    def configure(self, request):
        raise NotImplementedError

    @staticmethod
    def test_rights(resources, request=None):
        return True

    @staticmethod
    def get_fields():
        return []


class AnonimousAuthenticator(AbstractAuthenticator):
    " Anonymous access. Set identifier by IP address. "

    def authenticate(self, request):
        return True

    def configure(self, request):
        self.resource.auth = self
        self.resource.identifier = request.META.get('REMOTE_ADDR', 'anonymous')


class UserLoggedInAuthenticator(AbstractAuthenticator):
    " Check auth by session. "

    def __init__(self, *args, **kwargs):
        self.user = None
        super(UserLoggedInAuthenticator, self).__init__(*args, **kwargs)

    def authenticate(self, request):
        user = getattr(request, 'user', None)
        return user and user.is_active

    def configure(self, request):
        self.user = request.user
        self.resource.auth = self
        self.resource.identifier = self.user.username


class BasicAuthenticator(UserLoggedInAuthenticator):
    " HTTP Basic authentication. "

    def authenticate(self, request=None):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2 and auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user and user.is_active:
                    request.user = user
                    return True

        return False


class UserAuthenticator(UserLoggedInAuthenticator):
    " Authorization by login and password "

    username_fieldname = 'username'
    password_fieldname = 'password'

    def authenticate(self, request=None):
        try:
            username = request.REQUEST.get(self.username_fieldname)
            password = request.REQUEST.get(self.password_fieldname)
            request.user = authenticate(username=username, password=password)
            return request.user and request.user.is_active

        except KeyError:
            return False

    @classmethod
    def get_fields(cls):
        return [(cls.username_fieldname, dict(required=True)), (cls.password_fieldname, dict(required=True))]


class AccessKeyAuthenticator(UserLoggedInAuthenticator):
    " Authorization by API token. "

    def authenticate(self, request=None):
        """ Authenticate user using AccessKey from HTTP Header or GET params.
        """
        try:
            token = request.META.get('HTTP_AUTHORIZATION') or request.REQUEST['key']
            accesskey = AccessKey.objects.select_related('user').get(key=token)
            request.user = accesskey.user
            return request.user and request.user.is_active

        except(KeyError, AccessKey.DoesNotExist):
            return False
