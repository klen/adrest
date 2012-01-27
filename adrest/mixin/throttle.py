from adrest.utils import status
from adrest.utils.exceptions import HttpError
from adrest.utils.throttle import BaseThrottle


class ThrottleMeta(type):
    def __new__(mcs, name, bases, params):

        cls = super(ThrottleMeta, mcs).__new__(mcs, name, bases, params)
        assert issubclass(cls.throttle, BaseThrottle), "'throttle' must be subclass of BaseThrottle"
        return cls


class ThrottleMixin(object):

    __metaclass__ = ThrottleMeta

    throttle = BaseThrottle

    def throttle_check(self):
        throttle = self.throttle()
        wait = throttle.should_be_throttled(self.identifier)
        if wait:
            raise HttpError("Throttled, wait %d seconds." % wait, status=status.HTTP_503_SERVICE_UNAVAILABLE)
