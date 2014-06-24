""" ADRest authentication support.
"""
from ..settings import ADREST_ALLOW_OPTIONS
from ..utils import status
from ..utils.meta import MixinBaseMeta
from ..utils.auth import AnonimousAuthenticator, AbstractAuthenticator
from ..utils.exceptions import HttpError
from ..utils.tools import as_tuple


__all__ = 'AuthMixin',


class AuthMeta(MixinBaseMeta):

    """ Convert cls.meta.authenticators to tuple and check them. """

    def __new__(mcs, name, bases, params):
        cls = super(AuthMeta, mcs).__new__(mcs, name, bases, params)

        cls._meta.authenticators = as_tuple(cls._meta.authenticators)

        if not cls._meta.authenticators:
            raise AssertionError("Should be defined at least one authenticator.")

        for a in cls._meta.authenticators:
            if not issubclass(a, AbstractAuthenticator):
                raise AssertionError("Meta.authenticators should be subclasses of "
                                     "`adrest.utils.auth.AbstractAuthenticator`")

        return cls


class AuthMixin(object):

    """ Adds pluggable authentication behaviour. """

    __metaclass__ = AuthMeta

    class Meta:
        authenticators = AnonimousAuthenticator

    def __init__(self, *args, **kwargs):
        self.auth = None

    def authenticate(self, request):
        """ Attempt to authenticate the request.

        :param request: django.http.Request instance

        :return bool: True if success else raises HTTP_401

        """
        authenticators = self._meta.authenticators

        if request.method == 'OPTIONS' and ADREST_ALLOW_OPTIONS:
            self.auth = AnonimousAuthenticator(self)
            return True

        error_message = "Authorization required."
        for authenticator in authenticators:
            auth = authenticator(self)
            try:
                if not auth.authenticate(request):
                    raise AssertionError(error_message)

                self.auth = auth
                auth.configure(request)
                return True
            except AssertionError, e:
                error_message = str(e)

        raise HttpError(error_message, status=status.HTTP_401_UNAUTHORIZED)

    def check_rights(self, resources, request=None):
        """ Check rights for resources.

        :return bool: True if operation is success else HTTP_403_FORBIDDEN

        """
        if not self.auth:
            return True

        try:
            if not self.auth.test_rights(resources, request=request):
                raise AssertionError()

        except AssertionError, e:
            raise HttpError("Access forbiden. {0}".format(e), status=status.HTTP_403_FORBIDDEN)
