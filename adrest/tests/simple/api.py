from adrest.api import Api
from adrest.views import ResourceView

from .models import Task


class TaskResource(ResourceView):
    model = Task


API = Api()

API.register(TaskResource)
