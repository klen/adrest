from django.db import models

from adrest import settings
from adrest.signals import api_request_finished


# Preloads ADREST tags
try:
    from django.template.base import builtins
    from .templatetags import register

    builtins.append(register)

except ImportError:
    pass


# Access log
# -----------
if settings.ACCESS_LOG:

    class Access(models.Model):
        """ Log api queries.
        """
        created_at = models.DateTimeField(auto_now_add=True)
        uri = models.CharField(max_length=100)
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
        identifier = models.CharField(max_length=255)

        class Meta():
            ordering = ["-created_at"]
            verbose_name_plural = "Access"

        def __unicode__(self):
            return "#%s %s:%s:%s" % (self.pk, self.method, self.status_code, self.uri)

    def save_log(sender, response=None, request=None, **resources):

        resource = sender

        if not resource.log:
            return

        Access.objects.create(
            uri=request.path_info,
            method=request.method,
            version=str(resource.api),
            status_code=response.status_code,
            request='%s\n\n%s' % (str(request.META), str(getattr(request, 'data', ''))),
            identifier=resource.identifier or request.META.get('REMOTE_ADDR', 'anonymous'),
            response=response.content.decode('utf-8')[:5000],
        )

    api_request_finished.connect(save_log)


# Access keys
# -----------
if settings.ACCESSKEY:

    import uuid
    from django.contrib.auth.models import User

    class AccessKey(models.Model):
        """ API key.
        """
        key = models.CharField(max_length=40, blank=True)
        user = models.ForeignKey(User)
        created = models.DateTimeField(auto_now_add=True)

        class Meta():
            ordering = ["-created"]
            unique_together = 'user', 'key'

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
    if settings.AUTO_CREATE_ACCESSKEY:
        models.signals.post_save.connect(create_api_key, sender=User)


# pymode:lint_ignore=W0704
