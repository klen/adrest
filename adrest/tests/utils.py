""" ADRest test's helpers. """
from StringIO import StringIO
from urlparse import urlparse
from collections import defaultdict

from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import Model
from django.test import TestCase, client
from django.utils import simplejson
from django.utils.http import urlencode
from django.utils.functional import curry
from django.utils.encoding import smart_str


__all__ = 'AdrestRequestFactory', 'AdrestClient', 'AdrestTestCase'


def generic_method(
    rf, path, data=None, content_type=client.MULTIPART_CONTENT, follow=False,
        method='PUT', **extra):
    """ Fix django.

    :return request: request

    """

    if content_type is client.MULTIPART_CONTENT:
        data = rf._encode_data(data, content_type)
    else:
        data = smart_str(data, encoding=settings.DEFAULT_CHARSET)

    parsed = urlparse(path)
    r = {
        'CONTENT_LENGTH': len(data),
        'CONTENT_TYPE': content_type,
        'PATH_INFO': rf._get_path(parsed),
        'QUERY_STRING': parsed[4],
        'REQUEST_METHOD': method,
        'wsgi.input': FakePayload(data),
    }
    r.update(extra)
    return rf.request(**r)


class AdrestRequestFactory(client.RequestFactory):

    """ Path methods. """

    put = curry(generic_method, method="PUT")
    patch = curry(generic_method, method="PATCH")


class AdrestClient(client.Client):

    """ Patch client. """

    def put(self, path, data=None, content_type=client.MULTIPART_CONTENT,
            follow=False, method='PUT', **extra):
        """ Implement PUT.

        :return response: A result.

        """

        data = data or dict()
        response = generic_method(
            self, path, data=data, content_type=content_type, follow=follow,
            method=method, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response

    patch = curry(put, method='PATCH')

    def delete(self, path, data=None, **extra):
        """ Implement DELETE.

        :return response: A result.

        """

        data = data or dict()

        parsed = urlparse(path)
        r = {
            'PATH_INFO':       self._get_path(parsed),
            'QUERY_STRING':    urlencode(data, doseq=True) or parsed[4],
            'REQUEST_METHOD': 'DELETE',
        }
        r.update(extra)
        return self.request(**r)


class AdrestTestCase(TestCase):

    """ TestCase for ADRest related tests. """

    api = None
    client_class = AdrestClient

    @classmethod
    def reverse(cls, resource, **resources):
        """ Reverse resource by ResourceClass or name.

        :param resource: Resource Class or String name.
        :param **resources: Uri params

        :return str: URI string

        """
        if not cls.api:
            raise AssertionError("AdrestTestCase must have the api attribute.")

        if isinstance(resource, basestring):
            url_name = resource
            if not cls.api.resources.get(url_name):
                raise AssertionError("Invalid resource name: %s" % url_name)

        else:
            url_name = resource._meta.url_name

        params = dict()
        query = defaultdict(list)

        for name, resource in resources.items():

            if isinstance(resource, Model):
                resource = resource.pk

            if name in params:
                query[name].append(params[name])
                query[name].append(resource)
                del params[name]
                continue

            params[name] = resource

        name_ver = '' if not str(cls.api) else '%s-' % str(cls.api)
        uri = reverse(
            '%s-%s%s' % (cls.api.prefix, name_ver, url_name), kwargs=params)

        if query:
            uri += '?'
            for name, values in query:
                uri += '&'.join('%s=%s' % (name, value) for value in values)

        return uri

    def get_params(self, resource, headers=None, data=None, key=None, **kwargs):  # nolint
        headers = headers or dict()
        data = data or dict()
        if isinstance(key, Model):
            key = key.key
        headers['HTTP_AUTHORIZATION'] = key or headers.get(
            'HTTP_AUTHORIZATION')
        resource = self.reverse(resource, **kwargs)
        return resource, headers, data

    def get_resource(self, resource, method='get', data=None, headers=None, json=False, **kwargs):  # nolint
        """ Simply run resource method.

        :param resource: Resource Class or String name.
        :param data: Request data
        :param json: Make JSON request
        :param headers: Request headers
        :param key: HTTP_AUTHORIZATION token

        :return object: result

        """
        method = getattr(self.client, method)
        resource, headers, data = self.get_params(
            resource, headers, data, **kwargs)

        # Support JSON request
        if json:
            headers['content_type'] = 'application/json'
            data = simplejson.dumps(data)

        response = method(resource, data=data, **headers)
        return self._jsonify(response)

    def rpc(self, resource, rpc=None, headers=None, callback=None, **kwargs):
        """ Emulate RPC call.

        :param resource: Resource Class or String name.
        :param rpc: RPC params.
        :param headers: Send headers
        :param callback: JSONP callback

        :return object: result

        """
        resource, headers, data = self.get_params(
            resource, headers, data=rpc, **kwargs)

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

        response = method(
            resource, data=data, content_type='application/json', **headers)
        return self._jsonify(response)

    @staticmethod
    def _jsonify(response):
        if response.get('Content-type') == 'application/json':
            try:
                response.json = simplejson.loads(response.content)
            except ValueError:
                return response
        return response

    put_resource = curry(get_resource, method='put')
    post_resource = curry(get_resource, method='post')
    patch_resource = curry(get_resource, method='patch')
    delete_resource = curry(get_resource, method='delete')


class FakePayload(object):

    """ Fake payload.

    A wrapper around StringIO that restricts what can be read since data from
    the network can't be seeked and cannot be read outside of its content
    length. This makes sure that views can't do anything under the test client
    that wouldn't work in Real Life.

    """

    def __init__(self, content):
        self.__content = StringIO(content)
        self.__len = len(content)

    def read(self, num_bytes=None):
        """ READ.

        :return str: content

        """
        if num_bytes is None:
            num_bytes = self.__len or 0
        assert self.__len >= num_bytes, "Cannot read more than the available bytes from the HTTP incoming data."  # nolint
        content = self.__content.read(num_bytes)
        self.__len -= num_bytes
        return content

# lint_ignore=W0212,F0401
