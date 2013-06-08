""" Meta support for ADRest classes.
"""


__all__ = 'MetaBase',


class MetaBase(type):

    """ Init meta options. """

    def __new__(mcs, name, bases, params):
        meta = params['_meta'] = params.get('_meta', MetaOptions())
        cls = super(MetaBase, mcs).__new__(mcs, name, bases, params)

        meta = dict()
        for parent in reversed(cls.mro()):
            pmeta = getattr(parent, 'Meta', FakeMeta)
            meta.update(pmeta.__dict__)

        cls._meta.update({
            attr: meta[attr] for attr in meta
            if not attr.startswith('_')
        })

        return cls


class MetaOptions(dict):

    """ Resource meta options. """

    def __getattr__(self, name):
        return self.get(name)

    __setattr__ = dict.__setitem__


class FakeMeta:

    """ Fake meta data. """

    pass

# lint_ignore=W0212
