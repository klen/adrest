""" Generate a resource's map. """
from django.forms.models import ModelChoiceField
from django.utils.encoding import smart_unicode

from ..settings import ADREST_MAP_TEMPLATE
from ..utils.auth import AnonimousAuthenticator
from ..utils.emitter import HTMLTemplateEmitter, JSONEmitter
from ..views import ResourceView


__all__ = 'MapResource',


class MapResource(ResourceView):

    """ Simple Api Map. """

    class Meta:
        authenticators = AnonimousAuthenticator
        emit_template = ADREST_MAP_TEMPLATE
        emitters = HTMLTemplateEmitter, JSONEmitter
        log = False
        url_regex = r'^map$'

    def get(self, *args, **Kwargs):
        """ Render map.

        :return list: list of resources.

        """
        return list(self.__gen_apimap())

    def __gen_apimap(self):
        for url_name in sorted(self.api.resources.iterkeys()):
            resource = self.api.resources[url_name]
            info = dict(
                resource=resource,
                url_name=resource._meta.url_name,
                allowed_methods=resource._meta.allowed_methods,
                doc=resource.__doc__,
                emitters=', '.join(
                    [e.media_type for e in resource._meta.emitters]),
                fields=[],
                model=None,
            )
            if resource._meta.model:
                info['model'] = dict(
                    name="{0}.{1}".format(
                        resource._meta.model._meta.module_name, # nolint
                        resource._meta.model._meta.object_name, # nolint
                    ),
                    fields=resource._meta.model._meta.fields # nolint
                )

            models = [
                p._meta.model for p in resource._meta.parents if p._meta.model]

            if resource._meta.form and (
                'POST' in resource._meta.allowed_methods
                    or 'PUT' in resource._meta.allowed_methods):
                info['fields'] += [
                    (name, dict(
                        required=f.required and f.initial is None,
                        label=f.label,
                        help=smart_unicode(f.help_text + ''))
                     )
                    for name, f in resource._meta.form.base_fields.iteritems()
                    if not (isinstance(f, ModelChoiceField)
                            and f.choices.queryset.model in models)
                ]

            for a in resource._meta.authenticators:
                info['fields'] += a.get_fields()

            info['auth'] = set(
                a.__doc__ or 'Custom' for a in resource._meta.authenticators)

            key = resource._meta.url_regex\
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

# lint_ignore=W0212
