from ..settings import ALLOW_OPTIONS
from ..utils import status
from ..utils.auth import AnonimousAuthenticator, AbstractAuthenticator
from ..utils.exceptions import HttpError
from ..utils.tools import as_tuple


def check_authenticators(authenticators):
    authenticators = as_tuple(authenticators)
    for a in authenticators:
        assert issubclass(a, AbstractAuthenticator), "Authenticators must be subclasses of AbstractAuthenticator"
    return authenticators


class AuthMeta(type):

    def __new__(mcs, name, bases, params):
        cls = super(AuthMeta, mcs).__new__(mcs, name, bases, params)
        cls.authenticators = check_authenticators(cls.authenticators)
        return cls


class AuthMixin(object):
    " Adds pluggable authentication behaviour "

    __metaclass__ = AuthMeta

    authenticators = AnonimousAuthenticator
    auth = None
    identifier = ''

    def authenticate(self, request):
        """ Attempt to authenticate the request, returning an authentication context or None.
            An authentication context may be any object, although in many cases it will simply be a :class:`User` instance.
        """
        authenticators = self.authenticators
        self.identifier = request.META.get('REMOTE_ADDR', 'anonymous')

        if request.method == 'OPTIONS' and ALLOW_OPTIONS:
            self.auth = AnonimousAuthenticator(self)
            return True

        error_message = "Authorization required."
        for authenticator in authenticators:
            auth = authenticator(self)
            try:
                assert auth.authenticate(request), error_message
                self.auth = auth
                auth.configure(request)
                return True
            except AssertionError, e:
                error_message = str(e)

        raise HttpError(error_message, status=status.HTTP_401_UNAUTHORIZED)

    def check_rights(self, resources, request=None):
        " Check rights of client for queried resources "
        if not self.auth:
            return True

        try:
            assert self.auth.test_rights(resources, request=request)
        except AssertionError, e:
            raise HttpError("Access forbidden. %s" % str(e), status=status.HTTP_403_FORBIDDEN)
