import json as js
from collections import defaultdict
from django.conf import settings
from django.core.urlresolvers import reverse as django_reverse
from django.db.models import Model
from django.test import client
from django.utils.encoding import smart_str
from django.utils.functional import curry
from django.utils.http import urlencode
from urlparse import urlparse


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def generic_method(rf, path, data=None, content_type=client.MULTIPART_CONTENT, follow=False,
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

    api = None

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

    def request_resource(self, resource, method='get', data=None, headers=None, json=False,
                         api=None, key=None, **kwargs):
        """ Simply request resource method.

        :param resource: Resource Class or String name.
        :param data: Request data
        :param json: Make JSON request
        :param headers: Request headers
        :param client: Test client
        :param api: Resource API
        :param key: HTTP_AUTHORIZATION token

        :return object: result

        """
        method = getattr(self, method)
        headers = headers or dict()
        api = api or self.api

        if isinstance(key, Model):
            key = key.key

        headers['HTTP_AUTHORIZATION'] = key or headers.get('HTTP_AUTHORIZATION')

        data = data or dict()

        # Support JSON request
        if json:
            headers['content_type'] = 'application/json'
            data = js.dumps(data)

        url = self.reverse(resource, api=api, **kwargs)
        return jsonify(method(url, data=data, **headers))

    get_resource = request_resource
    put_resource = curry(request_resource, method='put')
    post_resource = curry(request_resource, method='post')
    patch_resource = curry(request_resource, method='patch')
    delete_resource = curry(request_resource, method='delete')

    def reverse(self, resource, api=None, **kwargs):
        api = api or self.api
        return reverse(resource, api=api, **kwargs)


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
        assert self.__len >= num_bytes, "Cannot read more than the available bytes from the HTTP incoming data."  # noqa
        content = self.__content.read(num_bytes)
        self.__len -= num_bytes
        return content


def reverse(resource, api=None, namespace=None, **resources):
    """ Reverse resource by ResourceClass or name string.

    :param resource: Resource Class or String name.
    :param api: API intance (if resource is string)
    :param namespace: Set namespace prefix
    :param **resources: Uri params

    :return str: URI string

    """
    if isinstance(resource, basestring):
        url_name = resource
        if not api:
            raise AssertionError("You sould send api parameter")

        if not api.resources.get(url_name):
            raise AssertionError("Invalid resource name: %s" % url_name)

    else:
        url_name = resource._meta.url_name
        api = resource.api

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

    name_ver = '' if not str(api) else '%s-' % str(api)
    ns_prefix = '' if not namespace else '%s:' % namespace
    uri = django_reverse(
        '%s%s-%s%s' % (ns_prefix, api.prefix, name_ver, url_name), kwargs=params)

    if query:
        uri += '?'
        for name, values in query:
            uri += '&'.join('%s=%s' % (name, value) for value in values)

    return uri


def jsonify(response):
    """ Check for request content is JSON. """
    if response.get('Content-type') == 'application/json':
        try:
            response.json = js.loads(response.content)
        except ValueError:
            return response
    return response

# pylama:ignore=D100,W0212,D102
