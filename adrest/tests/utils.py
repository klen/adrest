""" ADRest test's helpers. """
import json as js
from django.test import TestCase
from django.utils.functional import curry

from .client import AdrestClient, reverse


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
        return self.client.request_resource(resource, api=self.api, **kwargs)

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
                payload=js.dumps(data))

        else:
            headers['HTTP_ACCEPT'] = 'application/json'
            method = 'post'
            data = js.dumps(data)

        return self.client.request_resource(
            resource, method=method, data=data, headers=headers, api=self.api, key=key, **kwargs)

    put_resource = curry(get_resource, method='put')
    post_resource = curry(get_resource, method='post')
    patch_resource = curry(get_resource, method='patch')
    delete_resource = curry(get_resource, method='delete')
