import base64

from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.middleware.csrf import CsrfViewMiddleware

from adrest.utils import as_tuple, HttpError


class AuthenticatorMixin(object):
    """ Adds pluggable authentication behaviour.
    """
    authenticators = None

    def authenticate(self):
        if not self._authenticate():
            raise HttpError("Authorization required.", status=401)

    def _authenticate(self):
        """ Attempt to authenticate the request, returning an authentication context or None.
            An authentication context may be any object, although in many cases it will simply be a :class:`User` instance.
        """

        # Attempt authentication against each authenticator in turn,
        auth_result = True
        for authenticator in as_tuple(self.authenticators):
            auth_result = authenticator(self).authenticate()
            if auth_result:
                return auth_result

        return auth_result


class BaseAuthenticator(object):
    """ All authenticators should extend BaseAuthenticator.
    """
    message = "Authorization required."

    def __init__(self, resource):
        self.resource = resource

    def authenticate(self):
        return False


class AnonimousAuthenticator(BaseAuthenticator):
    """ Always return true.
    """
    def authenticate(self):
        return True


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
                    return user
        return False


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
            request.user = authenticate(username=username, password=password) or AnonymousUser()
            return request.user.is_authenticated()

        except KeyError:
            return False


class UserLoggedInAuthenticator(BaseAuthenticator):
    """ Use Djagno's built-in request session for authentication.
    """
    def authenticate(self):
        request = self.resource.request
        if getattr(request, 'user', None) and request.user.is_active:
            resp = CsrfViewMiddleware().process_view(request, None, (), {})
            if resp is None:  # csrf passed
                return request.user
        return None


try:
    from adrest.models import AccessKey
    from django.db import models

    class AccessKeyAuthenticator(BaseAuthenticator):
        """ Use AcessKey identification.
        """
        def authenticate(self):
            request = self.resource.request
            try:
                access_key = request.META.get('HTTP_AUTHORIZATION') or request.REQUEST['key']
                api_key = AccessKey.objects.get(key=access_key)
                request.user = api_key.user
                return True
            except(  KeyError, models.ObjectDoesNotExist ):
                return False

except ImportError:
    pass
