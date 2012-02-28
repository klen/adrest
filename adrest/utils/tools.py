def as_tuple(obj):
    " Given obj return a tuple "

    if not obj:
        return tuple()

    if isinstance(obj, (tuple, set, list)):
        return tuple(obj)

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
                    name = r.meta.name)

    for p in resource.url_params:
        yield '%(name)s/(?P<%(name)s>[^/]+)' % dict(name = p)

    if resource.prefix:
        yield resource.prefix

    yield '%(name)s/(?:(?P<%(name)s>[^/]+)/)?' % dict(name = resource.meta.name)
