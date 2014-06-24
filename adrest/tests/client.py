from django.conf import settings
from django.test import client
from django.utils.encoding import smart_str
from django.utils.functional import curry
from django.utils.http import urlencode
from urlparse import urlparse


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def generic_method(
        rf, path, data=None, content_type=client.MULTIPART_CONTENT,
        follow=False, method='PUT', **extra):
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

# pylama:ignore=D100,W0212,D102
