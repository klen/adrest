import collections


def as_tuple(obj):
    " Given obj return a tuple "

    if not obj:
        return tuple()

    if isinstance(obj, (tuple, set, list)):
        return tuple(obj)

    if hasattr(obj, '__iter__'):
        return obj

    return obj,


def gen_url_name(resource):
    " URL name for resource class generator. "
    if resource.parent:
        yield resource.parent.meta.url_name

    if resource.prefix:
        yield resource.prefix

    for p in resource.url_params:
        yield p

    yield resource.meta.name


def gen_url_regex(resource):
    " URL regex for resource class generator. "
    for r in resource.meta.parents:
        if r.url_regex:
            yield r.url_regex.rstrip('/$').lstrip('^')
        else:
            yield '%(name)s/(?P<%(name)s>[^/]+)' % dict(
                name=r.meta.name)

    for p in resource.url_params:
        yield '%(name)s/(?P<%(name)s>[^/]+)' % dict(name=p)

    if resource.prefix:
        yield resource.prefix

    yield '%(name)s/(?:(?P<%(name)s>[^/]+)/)?' % dict(name=resource.meta.name)


def fix_request(request):
    methods = "PUT", "PATCH"

    if request.method in methods and not getattr(request, request.method, None):

        if hasattr(request, '_post'):
            del(request._post)
            del(request._files)

        if hasattr(request, '_request'):
            del(request._request)

        request.method, method = "POST", request.method
        setattr(request, method, request.POST)
        request.method = method

    return request


class FrozenDict(collections.Mapping):
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
