ROOT_URLCONF = 'main.urls'
DATABASES =  {
        'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                    'USER': '',
                    'PASSWORD': '',
                    'TEST_CHARSET': 'utf8',
                }
            }
INSTALLED_APPS = 'django.contrib.auth', 'django.contrib.contenttypes', 'adrest', 'adrest.tests.main', 'adrest.tests.simple'
DEBUG = TEMPLATE_DEBUG = True
CACHE_BACKEND = 'locmem://'
ADREST_ACCESS_LOG = True
ADREST_ALLOW_OPTIONS = True
ADREST_AUTO_CREATE_ACCESSKEY = True
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
)

