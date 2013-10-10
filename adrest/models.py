""" ASRest related models. """
import uuid
from django.db import models
from django.contrib.auth.models import User

from .settings import ADREST_CONFIG


# Preloads ADREST tags
try:
    from django.template.base import builtins
    from .templatetags import register

    builtins.append(register)

except ImportError:
    pass


# Access log
# -----------
class Access(models.Model):
    """ Log api queries.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    uri = models.CharField(max_length=100, db_index=True)
    status_code = models.PositiveIntegerField()
    version = models.CharField(max_length=25)
    method = models.CharField(max_length=10, choices=(
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('OPTIONS', 'OPTIONS'),
    ))
    request = models.TextField()
    response = models.TextField()
    identifier = models.CharField(max_length=255, db_index=True)

    class Meta():
        ordering = ["-created_at"]
        verbose_name_plural = "Access"
        abstract = ADREST_CONFIG['ABSTRACT_ACCESS']


    def __unicode__(self):
        return "#{0} {1}:{2}:{3}".format(
            self.pk, self.method, self.status_code, self.uri)


# Access keys
# -----------
class AccessKey(models.Model):
    """ API key.
    """
    key = models.CharField(max_length=40, blank=True)
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)

    class Meta():
        ordering = ["-created"]
        unique_together = 'user', 'key'
        abstract = ADREST_CONFIG['ABSTRACT_ACCESS_KEY']

    def __unicode__(self):
        return u'#%s %s "%s"' % (self.pk, self.user, self.key)

    def save(self, **kwargs):
        self.key = self.key or str(uuid.uuid4()).replace('-', '')
        super(AccessKey, self).save(**kwargs)


# Auto create key for created user
def create_api_key(sender, created=False, instance=None, **kwargs):
    if created and instance:
        AccessKey.objects.create(user=instance)

# Connect create handler to user save event
if ADREST_CONFIG['AUTO_CREATE_ACCESSKEY'] and not ADREST_CONFIG['ABSTRACT_ACCESS_KEY']:
    models.signals.post_save.connect(create_api_key, sender=User)


# pymode:lint_ignore=W0704
