from django.template import Library, VariableDoesNotExist
from django.template.base import TagHelperNode, parse_bits
from django.template.loader import get_template


register = Library()

# Fix django templatetags module loader
__path__ = ""


class AdrestInclusionNode(TagHelperNode):

    def render(self, context):
        try:
            args, ctx = self.get_resolved_arguments(context)
            target = args[0]
            assert target
            ctx['content'] = target
        except (VariableDoesNotExist, AssertionError):
            return ''

        emitter = context.get('emitter')
        t_name = emitter.get_template_path(target)
        t = get_template(t_name)
        context.dicts.append(ctx)
        response = t.nodelist.render(context)
        context.pop()
        return response


def adrest_include(parser, token):
    " Include adrest_template for any objects. "
    bits = token.split_contents()[1:]
    args, kwargs = parse_bits(parser, bits, ['content'], 'args', 'kwargs', tuple(), False, 'adrest_include')
    return AdrestInclusionNode(False, args, kwargs)
adrest_include = register.tag(adrest_include)


def adrest_jsonify(content, **kwargs):
    " Serialize to JSON any object. "

    from adrest.utils.serializer import json_dumps
    return json_dumps(content)
adrest_jsonify = register.simple_tag(adrest_jsonify)
