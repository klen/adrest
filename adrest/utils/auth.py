import base64

from django.contrib.auth import authenticate
from django.middleware.csrf import CsrfViewMiddleware


class BaseAuthenticator(object):
    """ All authenticators should extend BaseAuthenticator.
    """
    message = "Authorization required."

    def __init__(self, resource):
        self.resource = resource
        self.identifier = ''

    def authenticate(self):
        return self.get_identifier()

    def get_identifier(self):
        return self.identifier

    @staticmethod
    def test_rights(resources, method):
        return True


class AnonimousAuthenticator(BaseAuthenticator):
    """ Always return true.
    """
    def get_identifier(self):
        return self.resource.request.META.get('REMOTE_ADDR', 'anonymous')


class BasicAuthenticator(BaseAuthenticator):
    """ Use HTTP Basic authentication.
    """
    def authenticate(self):
        request = self.resource.request
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2 and auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    self.identifier = user.username
        return self.get_identifier()


class UserAuthenticator(BaseAuthenticator):
    """ Django user authenticate.
    """
    username_fieldname = 'username'
    password_fieldname = 'password'

    def authenticate(self):
        request = self.resource.request
        try:
            username = request.REQUEST.get(self.username_fieldname)
            password = request.REQUEST.get(self.password_fieldname)
            request.user = authenticate(username=username, password=password)
            self.identifier = request.user.username if request.user else ''
        except KeyError:
            pass
        return self.get_identifier()


class UserLoggedInAuthenticator(BaseAuthenticator):
    """ Use Djagno's built-in request session for authentication.
    """
    def authenticate(self):
        request = self.resource.request
        if getattr(request, 'user', None) and request.user.is_active:
            resp = CsrfViewMiddleware().process_view(request, None, (), {})
            if resp is None:  # csrf passed
                self.identifier = request.user.username
        return self.get_identifier()


try:
    from adrest.models import AccessKey
    from django.core.exceptions import ObjectDoesNotExist


    class AccessKeyAuthenticator(BaseAuthenticator):
        """ Use AccessKey identification.
        """

        def authenticate(self):
            """ Authenticate user using AccessKey from HTTP Header or GET params.
            """
            request = self.resource.request
            try:
                access_key = request.META.get('HTTP_AUTHORIZATION') or request.REQUEST['key']
                api_key = AccessKey.objects.get(key=access_key)
                if self.test_user(api_key.user):
                    request.user = api_key.user
                    self.identifier = request.user.username
            except(KeyError, ObjectDoesNotExist):
                pass
            return self.get_identifier()

        def test_user(self, user):
            """ In this method you can implement User class check if you have
                several User classes with FK to AccessKey.

                With this you can use multiple AccessKeyAuthenticator classes for
                the resource and get the right class according to the test in this
                function.

                By default: doesn't care, if we find User by AccessKey, authenticate him
            """
            return True

except ImportError:
    pass
