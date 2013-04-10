from django.forms.models import ModelChoiceField
from django.utils.encoding import smart_unicode

from ..settings import MAP_TEMPLATE
from ..utils.auth import AnonimousAuthenticator
from ..utils.emitter import HTMLTemplateEmitter, JSONEmitter
from ..views import ResourceView


__all__ = 'MapResource',


class MapResource(ResourceView):
    " Simple Api Map. "

    log = False
    emitters = HTMLTemplateEmitter, JSONEmitter
    authenticators = AnonimousAuthenticator
    template = MAP_TEMPLATE

    url_regex = r'^map$'

    def get(self, *args, **Kwargs):
        return list(self.gen_apimap())

    def gen_apimap(self):
        for url_name in sorted(self.api.resources.iterkeys()):
            resource = self.api.resources[url_name]
            info = dict(
                resource=resource,
                doc=resource.__doc__,
                emitters=', '.join([e.media_type for e in resource.emitters]),
                fields=[],
                model=None,
            )
            if resource.model:
                info['model'] = dict(
                    name="{0}.{1}".format(
                        resource.model._meta.module_name, # nolint
                        resource.model._meta.object_name, # nolint
                    ),
                    fields=resource.model._meta.fields # nolint
                )

            models = [p.model for p in resource.meta.parents if p.model]

            if resource.form and (
                'POST' in resource.allowed_methods
                    or 'PUT' in resource.allowed_methods):
                info['fields'] += [
                    (name, dict(
                        required=f.required and f.initial is None,
                        label=f.label,
                        help=smart_unicode(f.help_text + ''))
                     )
                    for name, f in resource.form.base_fields.iteritems()
                    if not (isinstance(f, ModelChoiceField)
                            and f.choices.queryset.model in models)
                ]

            for a in resource.authenticators:
                info['fields'] += a.get_fields()

            info['auth'] = set(
                a.__doc__ or 'Custom' for a in resource.authenticators)

            key = resource.meta.url_regex\
                .replace("(?P", "")\
                .replace("[^/]+)", "")\
                .replace("?:", "")\
                .replace("$", "")\
                .replace("^", "/")

            if getattr(resource, "methods", None):
                import inspect
                info['methods'] = dict()
                for name, method in resource.methods.items():
                    info['methods'][name] = inspect.getargspec(method)
            yield key, info
