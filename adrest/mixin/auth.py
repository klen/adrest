from adrest.utils import status
from adrest.utils.auth import AnonimousAuthenticator
from adrest.utils.exceptions import HttpError
from adrest.utils.tools import as_tuple


class AuthenticatorMixin(object):
    """ Adds pluggable authentication behaviour.
    """
    authenticators = AnonimousAuthenticator,
    identifier = ''
    auth = None

    def authenticate(self):
        """ Attempt to authenticate the request, returning an authentication context or None.
            An authentication context may be any object, although in many cases it will simply be a :class:`User` instance.
        """
        for authenticator in as_tuple(self.authenticators):
            auth = authenticator(self)
            result = auth.authenticate()
            if result:
                self.auth = auth
                return result
        else:
            raise HttpError("Authorization required.", status=status.HTTP_401_UNAUTHORIZED)

        return True

    def check_rights(self, resources, method):
        if self.auth:
            mresources = [resources.get(m._meta.module_name) for m in self.meta.models if resources.get(m._meta.module_name)]
            try:
                assert self.auth.test_rights(mresources, method)
            except AssertionError:
                raise HttpError("Access forbidden.", status=status.HTTP_403_FORBIDDEN)
        return True
