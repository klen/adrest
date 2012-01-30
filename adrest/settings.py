" Adrest API settings. "
from django.conf import settings

from adrest.utils.tools import as_tuple


# Enable Adrest API logs
ACCESS_LOG = getattr(settings, 'ADREST_ACCESS_LOG', False)

# Auto create adrest access-key for created user
AUTO_CREATE_ACCESSKEY = getattr(settings, 'ADREST_AUTO_CREATE_ACCESSKEY', False)

# Max resources per page in list views
LIMIT_PER_PAGE = int(getattr(settings, 'ADREST_LIMIT_PER_PAGE', 50))

# Display django standart technical 500 page
DEBUG = getattr(settings, 'ADREST_DEBUG', False)
MAIL_ERRORS = as_tuple(getattr(settings, 'ADREST_MAIL_ERRORS', 500))

# Limit request number per second from same identifier, null is not limited
THROTTLE_AT = getattr(settings, 'ADREST_THROTTLE_AT', 120)
THROTTLE_TIMEFRAME = getattr(settings, 'ADREST_THROTTLE_TIMEFRAME', 60)

# We do not restrict access for OPTIONS request.
ALLOW_OPTIONS = getattr(settings, 'ADREST_ALLOW_OPTIONS', False)
