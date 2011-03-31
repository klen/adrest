from django.db.models import Model
from django.forms.models import ModelForm


class PartitialForm(ModelForm):

    def __init__(self, data=None, instance=None, **kwargs):
        super(PartitialForm, self).__init__(data, instance=instance)
        for name in self.fields.keys():
            if kwargs.get(name):
                value = kwargs.get(name)
                data[name] = value if not isinstance(value, Model) else value.pk
            elif instance and getattr(instance, name) and not data.has_key(name):
                value = getattr(instance, name)
                data[name] = value if not isinstance(value, Model) else value.pk
        self.data = data
