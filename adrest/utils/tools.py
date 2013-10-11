import collections
from django.utils.importlib import import_module


def as_tuple(obj):
    " Given obj return a tuple "

    if not obj:
        return tuple()

    if isinstance(obj, (tuple, set, list)):
        return tuple(obj)

    if hasattr(obj, '__iter__') and not isinstance(obj, dict):
        return obj

    return obj,


def gen_url_name(resource):
    " URL name for resource class generator. "

    if resource._meta.parent:
        yield resource._meta.parent._meta.url_name

    if resource._meta.prefix:
        yield resource._meta.prefix

    for p in resource._meta.url_params:
        yield p

    yield resource._meta.name


def gen_url_regex(resource):
    " URL regex for resource class generator. "

    if resource._meta.parent:
        yield resource._meta.parent._meta.url_regex.rstrip('/$').lstrip('^')

    for p in resource._meta.url_params:
        yield '%(name)s/(?P<%(name)s>[^/]+)' % dict(name=p)

    if resource._meta.prefix:
        yield resource._meta.prefix

    yield '%(name)s/(?P<%(name)s>[^/]+)?' % dict(name=resource._meta.name)


def fix_request(request):
    methods = "PUT", "PATCH"

    if request.method in methods\
            and not getattr(request, request.method, None):

        if hasattr(request, '_post'):
            del(request._post)
            del(request._files)

        if hasattr(request, '_request'):
            del(request._request)

        request.method, method = "POST", request.method
        setattr(request, method, request.POST)
        request.method = method

    request.adrest_fixed = True

    return request


class FrozenDict(collections.Mapping): # nolint
    """ Immutable dict. """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # It would have been simpler and maybe more obvious to
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of
        # n we are going to run into, but sometimes it's hard to resist the
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            self._hash = 0
            for key, value in self.iteritems():
                self._hash ^= hash(key)
                self._hash ^= hash(value)
        return self._hash

    def __str__(self):
        return str(dict(self.iteritems()))

    def __repr__(self):
        return "<FrozenDict: %s>" % repr(dict(self.iteritems()))


def import_functions(paths):
    """Import notifiers

    :param notifiers: list of string
    :return: list of imported functions
    """

    res = []
    for notifier in paths:
        module, notifier_name = notifier.rsplit('.', 1)
        res.append(getattr(import_module(module), notifier_name, None))

    return res

