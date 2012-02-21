from django.template import Library, Node, Variable
from django.template.loader import get_template
from copy import copy


register = Library()

# Fix django templatetags module loader
__path__ = ""

class AdrestInclusionNode(Node):

    def __init__(self, name, *args):
        self.var = Variable(name)
        super(AdrestInclusionNode, self).__init__()

    def render(self, context):
        target = self.var.resolve(context)
        if not target:
            return ''

        emitter = context.get('emitter')
        t_name = emitter.get_template_path(target)
        t = get_template(t_name)
        context = copy(context)
        context['content'] = target
        return t.nodelist.render(context)


def adrest_include(parser, token):
    bits = token.split_contents()[1:]
    return AdrestInclusionNode(*bits)
adrest_include = register.tag(adrest_include)
