class MetaOptions(object):
    " Resource meta options "

    def __init__(self):
        self.name = ''
        self.url_name = ''
        self.url_regex = ''
        self.parents = []
        self.model_fields = set()

        self.emitters_dict = dict()
        self.emitters_types = []
        self.default_emitter = None

        self.parsers_dict = dict()
        self.default_parser = None

    def __str__(self):
        return "%(url_name)s(%(name)s) - %(url_regex)s %(parents)s" % self.__dict__

    __repr__ = __str__


def gen_url_name(resource):
    if resource.parent:
        yield resource.parent.meta.url_name

    if resource.prefix:
        yield resource.prefix

    for p in resource.url_params:
        yield p

    yield resource.meta.name


def gen_url_regex(resource):
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
