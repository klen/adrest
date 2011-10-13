from django.db.models import Model
from django.db.models.fields import AutoField
from django.db.models.fields.related import ManyToManyField
from django.forms.models import ModelForm


def get_initial_from_model(model, instance):
    gen = ((f.name, f.value_from_object(instance) if instance else f.get_default()) for f in model._meta.fields if not isinstance(f, (ManyToManyField, AutoField)))
    return dict(v for v in gen if not v[1] is None)


class PartitialForm(ModelForm):

    def __init__(self, data=None, instance=None, initial=None, prefix=None, label_suffix=':', empty_permitted=False, **kwargs):
        resources = dict((k, v if not isinstance(v, Model) else v.pk) for k, v in kwargs.iteritems())
        formdata = get_initial_from_model(self._meta.model, instance)
        formdata.update(data or dict())
        formdata.update(resources)
        super(PartitialForm, self).__init__(formdata, instance=instance, prefix=prefix, label_suffix=label_suffix, empty_permitted=empty_permitted)
