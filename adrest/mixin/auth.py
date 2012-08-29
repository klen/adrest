from ..settings import ALLOW_OPTIONS
from ..utils import status
from ..utils.auth import AnonimousAuthenticator, BaseAuthenticator
from ..utils.exceptions import HttpError
from ..utils.tools import as_tuple


def check_authenticators(authenticators):
    authenticators = as_tuple(authenticators)
    for a in authenticators:
        assert issubclass(a, BaseAuthenticator), "Authenticators must be subclasses of BaseAuthenticator"
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
    identifier = ''
    auth = None

    def authenticate(self, request):
        """ Attempt to authenticate the request, returning an authentication context or None.
            An authentication context may be any object, although in many cases it will simply be a :class:`User` instance.
        """
        authenticators = self.authenticators

        if request.method == 'OPTIONS' and ALLOW_OPTIONS:
            authenticators = AnonimousAuthenticator,

        for authenticator in authenticators:
            self.auth = authenticator(self)
            self.identifier = self.auth.authenticate(request)
            if self.identifier:
                return self.identifier

        self.auth, self.identifier = None, ''
        raise HttpError("Authorization required.", status=status.HTTP_401_UNAUTHORIZED)

    def check_rights(self, resources, request=None):
        " Check rights of client for queried resources "
        if not self.auth:
            return True

        try:
            assert self.auth.test_rights(resources, request=request)
        except AssertionError, e:
            raise HttpError("Access forbidden. %s" % str(e), status=status.HTTP_403_FORBIDDEN)
