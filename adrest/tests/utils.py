from StringIO import StringIO
from urlparse import urlparse

from django.core.urlresolvers import reverse
from django.db.models import Model
from django.test import TestCase, Client
from django.utils import simplejson
from django.utils.functional import curry


MULTIPART_CONTENT = 'multipart/form-data; boundary=BoUnDaRyStRiNg'


class AdrestClient(Client):

    def patch(self, path, data=None, content_type=MULTIPART_CONTENT, follow=False, **extra):
        " Send a resource to the server using PATCH. "

        data = data or dict()
        patch_data = self._encode_data(data, content_type)
        parsed = urlparse(path)
        r = {
            'CONTENT_LENGTH': len(patch_data),
            'CONTENT_TYPE': content_type,
            'PATH_INFO': self._get_path(parsed),
            'QUERY_STRING': parsed[4],
            'REQUEST_METHOD': 'PATCH',
            'wsgi.input': FakePayload(patch_data),
        }
        r.update(extra)
        response = self.request(**r)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response


class AdrestTestCase(TestCase):
    api = None

    def setUp(self):
        assert self.api, "AdrestTestCase must have the api attribute."
        self.client = AdrestClient()

    def reverse(self, resource, **kwargs):
        """ Reverse resource by ResourceClass or name.

            :param resource: Resource Class or String name.
            :param **kwargs: Uri params
        """
        if isinstance(resource, basestring):
            url_name = resource
            assert self.api.resources.get(url_name), "Invalid resource name: %s" % url_name

        else:
            url_name = resource.meta.url_name

        kwargs = dict((k, getattr(v, "pk", v)) for k, v in kwargs.iteritems())
        name_ver = '' if not str(self.api) else '%s-' % str(self.api)
        return reverse('%s-%s%s' % (self.api.prefix, name_ver, url_name), kwargs=kwargs)

    def get_params(self, resource, headers=None, data=None, key=None, **kwargs):
        headers = headers or dict()
        data = data or dict()
        if isinstance(key, Model):
            key = key.key
        headers['HTTP_AUTHORIZATION'] = key or headers.get('HTTP_AUTHORIZATION')
        resource = self.reverse(resource, **kwargs)
        return resource, headers, data

    def get_resource(self, resource, method='get', data=None, headers=None, **kwargs):
        """ Simply run resource method.

            :param resource: Resource Class or String name.
            :param data: Request data
            :param headers: Request headers
            :param key: HTTP_AUTHORIZATION token
        """
        method = getattr(self.client, method)
        resource, headers, data = self.get_params(resource, headers, data, **kwargs)
        return method(resource, data=data, **headers)

    def rpc(self, resource, rpc=None, headers=None, callback=None, **kwargs):
        """ Emulate RPC call.

            :param resource: Resource Class or String name.
            :param rpc: RPC params.
            :param headers: Send headers
            :param callback: JSONP callback
        """
        resource, headers, data = self.get_params(resource, headers, data=rpc, **kwargs)

        if callback:
            headers['HTTP_ACCEPT'] = 'text/javascript'
            method = self.client.get
            data = dict(
                callback=callback,
                payload=simplejson.dumps(data))

        else:
            headers['HTTP_ACCEPT'] = 'application/json'
            method = self.client.post
            data = simplejson.dumps(data)

        return method(resource, data=data, content_type='application/json', **headers)

    put_resource = curry(get_resource, method='put')
    post_resource = curry(get_resource, method='post')
    patch_resource = curry(get_resource, method='patch')
    delete_resource = curry(get_resource, method='delete')


class FakePayload(object):
    """
    A wrapper around StringIO that restricts what can be read since data from
    the network can't be seeked and cannot be read outside of its content
    length. This makes sure that views can't do anything under the test client
    that wouldn't work in Real Life.
    """
    def __init__(self, content):
        self.__content = StringIO(content)
        self.__len = len(content)

    def read(self, num_bytes=None):
        if num_bytes is None:
            num_bytes = self.__len or 0
        assert self.__len >= num_bytes, "Cannot read more than the available bytes from the HTTP incoming data."
        content = self.__content.read(num_bytes)
        self.__len -= num_bytes
        return content
