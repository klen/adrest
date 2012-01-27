from .models import Task
from adrest.api import Api
from adrest.utils import emitter
from adrest.views import ResourceView


class TaskResource(ResourceView):
    model = Task
    emitters = emitter.XMLTemplateEmitter


API = Api()
API.register(TaskResource)
