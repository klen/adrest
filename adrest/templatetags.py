from django.template import Library, Node, Variable, VariableDoesNotExist
from django.template.loader import get_template


register = Library()

# Fix django templatetags module loader
__path__ = ""

class AdrestInclusionNode(Node):

    def __init__(self, name, *args):
        self.var = Variable(name)
        super(AdrestInclusionNode, self).__init__()

    def render(self, context):
        try:
            target = self.var.resolve(context)
            assert target
        except (VariableDoesNotExist, AssertionError):
            return ''

        emitter = context.get('emitter')
        t_name = emitter.get_template_path(target)
        t = get_template(t_name)
        context.dicts.append(dict(content=target))
        response = t.nodelist.render(context)
        context.pop()
        return response


def adrest_include(parser, token):
    bits = token.split_contents()[1:]
    return AdrestInclusionNode(*bits)
adrest_include = register.tag(adrest_include)
