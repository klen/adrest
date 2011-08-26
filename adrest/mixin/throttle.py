from adrest.utils import status
from adrest.utils.exceptions import HttpError
from adrest.utils.throttle import BaseThrottle


class ThrottleMixin(object):

    throttle = BaseThrottle

    def throttle_check(self):
        throttle = self.throttle()
        wait = throttle.should_be_throttled(self.identifier)
        if wait:
            raise HttpError("Throttled, wait %d seconds." % wait, status=status.HTTP_503_SERVICE_UNAVAILABLE)
