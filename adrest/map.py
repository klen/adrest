from django.forms.models import ModelChoiceField
from django.utils.encoding import smart_unicode

from .utils.auth import AnonimousAuthenticator
from .utils.emitter import HTMLTemplateEmitter, JSONEmitter
from .views import ResourceView


class MapResource(ResourceView):
    " Simple Api Map. "

    log = False
    emitters = HTMLTemplateEmitter, JSONEmitter
    authenticators = AnonimousAuthenticator
    template = 'api/map.html'

    url_regex = r'^map$'

    def get(self, *args, **Kwargs):
        return self.api.str_version, list(self.gen_apimap())

    def gen_apimap(self):
        for url_name in sorted(self.api.resources.iterkeys()):
            resource = self.api.resources[url_name]
            info = dict(
                name = url_name,
                methods = resource.allowed_methods,
                fields = []
            )
            if resource.model:
                info['resource'] = resource.model.__name__

            models = [p.model for p in resource.meta.parents if p.model]

            if resource.form and ('POST' in resource.allowed_methods or 'PUT' in resource.allowed_methods):
                info['fields'] += [
                    (name, dict(
                        required = f.required and f.initial is None,
                        help = smart_unicode(f.help_text + ''))
                    )
                    for name, f in resource.form.base_fields.iteritems()
                    if not (isinstance(f, ModelChoiceField) and f.choices.queryset.model in models)
                ]

            for a in resource.authenticators:
                info['fields'] += a.get_fields()

            info['auth'] = set(map(str, resource.authenticators))
            key = resource.meta.url_regex.replace("(?P", "").replace("[^/]+)", "").replace("?:", "").replace("$", "")
            yield key, info
