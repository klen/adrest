from .models import Task
from adrest.api import Api
from adrest.utils import emitter
from adrest.views import ResourceView


class TaskResource(ResourceView):

    class Meta:
        model = Task
        emitters = emitter.XMLTemplateEmitter


class Task2Resource(ResourceView):

    class Meta:
        allowed_methods = 'GET', 'POST'
        model = Task
        emit_include = 'description'
        emitters = emitter.JSONEmitter

    @staticmethod
    def to_simple__description(task, serializer):
        return "{0} -- {1}".format(task.title, task.user.username)

    def to_simple(self, content, simple, serializer=None):
        simple['api'] = self.api.version
        return simple


API = Api(version='1.0b')
API.register(TaskResource)
API.register(Task2Resource, url_name='task2', url_regex='task2')

# lint_ignore=C
