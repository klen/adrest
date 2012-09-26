from ..utils import status
from ..utils.exceptions import HttpError
from ..utils.throttle import NullThrottle, AbstractThrottle


class ThrottleMeta(type):

    def __new__(mcs, name, bases, params):
        cls = super(ThrottleMeta, mcs).__new__(mcs, name, bases, params)
        assert issubclass(cls.throttle, AbstractThrottle), "'throttle' must be subclass of AbstractThrottle"
        return cls


class ThrottleMixin(object):

    __metaclass__ = ThrottleMeta

    throttle = NullThrottle

    def throttle_check(self):
        throttle = self.throttle()
        wait = throttle.should_be_throttled(self)
        if wait:
            raise HttpError("Throttled, wait %d seconds." % wait, status=status.HTTP_503_SERVICE_UNAVAILABLE)
