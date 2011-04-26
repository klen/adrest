from django.conf import settings
from django.contrib import admin
from django.db import models

from adrest.signals import api_request_finished


# Access log
# -----------
if settings.ADREST_ACCESSLOG:

    class Access(models.Model):
        """ Log api queries.
        """
        created_at = models.DateTimeField(auto_now_add=True)
        uri = models.CharField(max_length=100)
        status_code = models.PositiveIntegerField()
        method = models.CharField(max_length=10, choices=(
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('DELETE', 'DELETE'),
        ))
        request = models.TextField()
        response = models.TextField()
        identifier = models.CharField(max_length=255)

        def __unicode__(self):
            return "%s - %s" % (self.status_code, self.uri)

    class AccessAdmin(admin.ModelAdmin):
        list_display = 'status_code', 'uri', 'created_at'
    admin.site.register(Access, AccessAdmin)

    def save_log(sender, response=None, **kwargs):

        if not sender.log:
            return

        Access.objects.create(
            uri = sender.request.path_info,
            method = sender.request.method,
            status_code = response.status_code,
            request = str(getattr(sender.request, 'data', '')),
            identifier = sender.identifier or '',

            # Truncate response to 5000 symbols
            response = response.content[:5000].rsplit(None, 1)[0],
        )

    api_request_finished.connect(save_log)


# Access keys
# -----------
if 'django.contrib.auth' in settings.INSTALLED_APPS:

    import uuid
    from django.contrib.auth.models import User


    class AccessKey(models.Model):
        """ API key.
        """
        key =  models.CharField(max_length=40, blank=True)
        user = models.ForeignKey(User)
        created = models.DateTimeField(auto_now_add=True)

        class Meta():
            unique_together = 'user', 'key'

        def __unicode__(self):
            return u"%s for %s" % (self.key, self.user)

        def save(self, **kwargs):
            self.key = self.key or str(uuid.uuid4()).replace('-', '')
            super(AccessKey, self).save(**kwargs)

    admin.site.register(AccessKey)

    # Auto create key for created user
    def create_api_key(sender, created=False, instance=None, **kwargs):
        if created and instance:
            AccessKey.objects.create(user=instance)

    # Connect create handler to user save event
    if settings.ADREST_ACCESSKEY:
        models.signals.post_save.connect(create_api_key, sender=User)
