""" Safe API. """
from ..utils import status
from ..utils.meta import MixinBaseMeta
from ..utils.exceptions import HttpError
from ..utils.throttle import NullThrottle, AbstractThrottle

__all__ = 'ThrottleMixin',


class ThrottleMeta(MixinBaseMeta):

    """ Prepare throtles. """

    def __new__(mcs, name, bases, params):
        cls = super(ThrottleMeta, mcs).__new__(mcs, name, bases, params)

        if not issubclass(cls._meta.throttle, AbstractThrottle):
            raise AssertionError(
                "'cls.Meta.throttle' must be subclass of AbstractThrottle"
            )

        return cls


class ThrottleMixin(object):

    """ Throttle request. """

    __metaclass__ = ThrottleMeta

    class Meta:
        throttle = NullThrottle

    def throttle_check(self):
        """ Check for throttling. """
        throttle = self._meta.throttle()
        wait = throttle.should_be_throttled(self)
        if wait:
            raise HttpError(
                "Throttled, wait {0} seconds.".format(wait),
                status=status.HTTP_503_SERVICE_UNAVAILABLE)
