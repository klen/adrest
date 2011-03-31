from uuid import uuid1

from django.contrib.auth.models import User
from django.db import models


class Key(models.Model):
    """ API key.
    """
    key =  models.CharField(max_length=40, blank=True)
    user = models.ForeignKey(User)

    def save(self, **kwargs):
        self.key = self.key or str(uuid1())
        super(Key, self).save(**kwargs)


class Log(models.Model):
    """ Log api queries.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    uri = models.CharField(max_length=100)
    status_code = models.PositiveIntegerField()
    request = models.TextField()
    response = models.TextField()

    user = models.ForeignKey(User, null=True)

    def __unicode__(self):
        return "%s - %s" % (self.status_code, self.uri)
