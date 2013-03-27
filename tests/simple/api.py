from .models import Task
from adrest.api import Api
from adrest.utils import emitter
from adrest.views import ResourceView


class TaskResource(ResourceView):
    emitters = emitter.XMLTemplateEmitter
    model = Task


class Task2Resource(ResourceView):
    allowed_methods = 'GET', 'POST'
    emitters = emitter.JSONEmitter
    model = Task


API = Api(version='1.0b')
API.register(TaskResource)
API.register(Task2Resource, url_name='task2', url_regex='task2')
