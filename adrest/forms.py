""" Default ADRest form for Django models. """
from django.db.models import Model
from django.db.models.fields import AutoField
from django.db.models.fields.related import ManyToManyField
from django.forms.models import ModelForm


class PartitialForm(ModelForm):

    """ Default ADRest form for models.

    Allows partitial updates and parses a finded resources.

    """

    def __init__(self, data=None, instance=None, initial=None, prefix=None,
                 label_suffix=':', empty_permitted=False, **kwargs):

        formdata = self.__get_initial_from_model(instance)
        formdata.update(data or dict())

        resources = dict((k, v if not isinstance(
            v, Model) else v.pk) for k, v in kwargs.iteritems())
        formdata.update(resources)

        super(PartitialForm, self).__init__(
            formdata, instance=instance, prefix=prefix,
            label_suffix=label_suffix, empty_permitted=empty_permitted)

    def __get_initial_from_model(self, instance):
        required_fields = [
            f for f in self._meta.model._meta.fields
            if not isinstance(f, (ManyToManyField, AutoField))
        ]

        gen = (
            (f.name, f.value_from_object(instance) if instance
             else f.get_default()) for f in required_fields
        )
        return dict(item for item in gen if not item[1] is None)
