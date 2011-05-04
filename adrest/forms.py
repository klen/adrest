from django.db.models import Model
from django.db.models.fields.related import RelatedField
from django.forms.models import ModelForm


class PartitialForm(ModelForm):

    def __init__(self, data=None, instance=None, **kwargs):
        super(PartitialForm, self).__init__(data, instance=instance)
        for name in self.fields.keys():
            if kwargs.get(name):
                value = kwargs.get(name)
                data[name] = value if not isinstance(value, Model) else value.pk
            elif instance and not data.has_key(name):
                field = instance._meta.get_field(name)
                if isinstance(field, RelatedField):
                    data[name] = getattr(instance, '%s_id' % name)
                else:
                    data[name] = getattr(instance, name)
        self.data = data
