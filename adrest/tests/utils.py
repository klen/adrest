""" ADRest test's helpers. """
from collections import defaultdict
from django.core.urlresolvers import reverse as django_reverse
from django.db.models import Model
from django.test import TestCase
from django.utils import simplejson
from django.utils.functional import curry

from .client import AdrestClient


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

        return reverse(resource, cls.api, **resources)

    def get_resource(self, resource, **kwargs):
        """ Simply run resource method.

        :param resource: Resource Class or String name.
        :param data: Request data
        :param json: Make JSON request
        :param headers: Request headers
        :param key: HTTP_AUTHORIZATION token

        :return object: result

        """
        return request_resource(
            resource, api=self.api, client=self.client, **kwargs)

    def rpc(self, resource, rpc=None, headers=None, callback=None, key=None,
            **kwargs):
        """ Emulate RPC call.

        :param resource: Resource Class or String name.
        :param rpc: RPC params.
        :param headers: Send headers
        :param callback: JSONP callback

        :return object: result

        """
        data = rpc or dict()
        headers = headers or dict()
        headers['content_type'] = 'application/json'

        if callback:
            headers['HTTP_ACCEPT'] = 'text/javascript'
            method = 'get'
            data = dict(
                callback=callback,
                payload=simplejson.dumps(data))

        else:
            headers['HTTP_ACCEPT'] = 'application/json'
            method = 'post'
            data = simplejson.dumps(data)

        return request_resource(
            resource, method=method, data=data, headers=headers,
            client=self.client, api=self.api, key=key, **kwargs)

    put_resource = curry(get_resource, method='put')
    post_resource = curry(get_resource, method='post')
    patch_resource = curry(get_resource, method='patch')
    delete_resource = curry(get_resource, method='delete')


def reverse(resource, api=None, **resources):
    """ Reverse resource by ResourceClass or name string.

    :param resource: Resource Class or String name.
    :param api: API intance (if resource is string)
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
    uri = django_reverse(
        '%s-%s%s' % (api.prefix, name_ver, url_name), kwargs=params)

    if query:
        uri += '?'
        for name, values in query:
            uri += '&'.join('%s=%s' % (name, value) for value in values)

    return uri


def request_resource(resource, method='get', data=None, headers=None,
                     json=False, client=None, api=None, key=None, **kwargs):
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
    if client is None:
        client = AdrestClient()

    method = getattr(client, method)
    headers = headers or dict()

    if isinstance(key, Model):
        key = key.key

    headers['HTTP_AUTHORIZATION'] = key or headers.get('HTTP_AUTHORIZATION')

    data = data or dict()

    # Support JSON request
    if json:
        headers['content_type'] = 'application/json'
        data = simplejson.dumps(data)

    url = reverse(resource, api=api, **kwargs)
    return jsonify(method(url, data=data, **headers))


def jsonify(response):
    """ Check for request content is JSON. """
    if response.get('Content-type') == 'application/json':
        try:
            response.json = simplejson.loads(response.content)
        except ValueError:
            return response
    return response

# pylama:ignore=C901,W0212
