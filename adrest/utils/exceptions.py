from django.core.exceptions import ValidationError

from .status import HTTP_400_BAD_REQUEST


class HttpError(Exception):
    " Represents HTTP Error. "

    def __init__(self, content, status=HTTP_400_BAD_REQUEST, emitter=None):
        self.content, self.status, self.emitter = content, status, emitter
        super(HttpError, self).__init__(content)

    def __str__(self):
        return self.content

    __repr__ = __str__


class FormError(ValidationError):
    " Represents Form Error. "

    def __init__(self, form, emitter=None):
        self.form, self.emitter = form, emitter
        super(FormError, self).__init__(form.errors.as_text())
