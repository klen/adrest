import abc
import time
import hashlib

from django.core.cache import cache

from ..settings import THROTTLE_AT, THROTTLE_TIMEFRAME


class AbstractThrottle(object):
    """ Fake throttle class.
    """

    __meta__ = abc.ABCMeta

    throttle_at = THROTTLE_AT
    timeframe = THROTTLE_TIMEFRAME

    @abc.abstractmethod
    def should_be_throttled(self, resource):
        """ Returns whether or not the user has exceeded their throttle limit.
        """
        pass

    @staticmethod
    def convert_identifier_to_key(identifier):
        """ Takes an identifier (like a username or IP address) and converts it
            into a key usable by the cache system.
        """
        key = ''.join(c for c in identifier if c.isalnum() or c in '_.-')
        if len(key) > 230:
            key = key[:150] + '-' + hashlib.md5(key).hexdigest()

        return "%s_accesses" % key


class NullThrottle(AbstractThrottle):
    " Anybody never be throttled. "

    @staticmethod
    def should_be_throttled(resource):
        return 0


class CacheThrottle(AbstractThrottle):
    """ A throttling mechanism that uses just the cache.
    """
    def should_be_throttled(self, resource):
        key = self.convert_identifier_to_key(resource.identifier)
        count, expiration, now = self._get_params(key)
        if count >= self.throttle_at and expiration > now:
            return expiration - now

        cache.set(key, (count + 1, expiration), (expiration - now))
        return 0

    def _get_params(self, key):
        count, expiration = cache.get(key, (1, None))
        now = time.time()
        if expiration is None:
            expiration = now + self.timeframe
        return count, expiration, now
