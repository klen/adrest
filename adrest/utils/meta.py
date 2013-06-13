""" Meta support for ADRest classes.
"""
from django.db.models import get_model, Model


__all__ = 'MixinBaseMeta', 'MixinBase'


class MetaOptions(dict):

    """ Storage for Meta options. """

    def __getattr__(self, name):
        return self.get(name)

    __setattr__ = dict.__setitem__


class Meta:

    """ Base options for all ADRest mixins.

    With Meta options you can setup your resources.

    """

    # Link to parent resource. Used for create a resource's hierarchy.
    parent = None

    #: Setup Django ORM model.
    #: Value could be a model class or string path like 'app.model'.
    model = None


class MixinBaseMeta(type):

    """ Init meta options.

    Merge Meta options from class bases.

    """

    def __new__(mcs, name, bases, params):
        params['_meta'] = params.get('_meta', MetaOptions())
        cls = super(MixinBaseMeta, mcs).__new__(mcs, name, bases, params)

        meta = dict()
        for parent in reversed(cls.mro()):
            if hasattr(parent, 'Meta'):
                meta.update(parent.Meta.__dict__)

        cls._meta.update(dict(
            (attr, meta[attr]) for attr in meta
            if not attr.startswith('_')
        ))

        # Prepare hierarchy
        cls._meta.parents = []
        if cls._meta.parent:
            cls._meta.parents = (
                cls._meta.parent._meta.parents + [cls._meta.parent])

        if not cls._meta.model:
            return cls

        # Create model from string
        if isinstance(cls._meta.model, basestring):
            if not '.' in cls._meta.model:
                raise AssertionError(
                    "'model_class' must be either a model"
                    " or a model name in the format"
                    " app_label.model_name")
            cls._meta.model = get_model(*cls._meta.model.split("."))

        # Check meta.name and queryset
        if not issubclass(cls._meta.model, Model):
            raise AssertionError("'model' attribute must be subclass of Model")

        cls._meta.fields = set(f.name for f in cls._meta.model._meta.fields)

        return cls


class MixinBase(object):

    """ Base class for all ADRest mixins.

    .. autoclass:: adrest.utils.meta.Meta
       :members:

    """

    Meta = Meta

    __metaclass__ = MixinBaseMeta

    __parent__ = None

    @property
    def parent(self):
        """ Cache a instance of self parent class.

        :return object: instance of self.Meta.parent class

        """
        if not self._meta.parent:
            return None

        if not self.__parent__:
            self.__parent__ = self._meta.parent()

        return self.__parent__
