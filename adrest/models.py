from django.conf import settings
from django.contrib import admin
from django.db import models

from adrest.signals import api_request


# Access log
# -----------
if settings.ADREST_ACCESSLOG:

    class Access(models.Model):
        """ Log api queries.
        """
        created_at = models.DateTimeField(auto_now_add=True)
        uri = models.CharField(max_length=100)
        status_code = models.PositiveIntegerField()
        request = models.TextField()
        response = models.TextField()
        identifier = models.CharField(max_length=255)

        def __unicode__(self):
            return "%s - %s" % (self.status_code, self.uri)

    admin.site.register(Access)

    def save_log(sender, response, **kwargs):
        Access.objects.create(
            uri = sender.request.path_info,
            status_code = response.status_code,
            request = sender.request.raw_post_data,
            response = response.content,
            identifier = sender.identifier or '',
        )

    api_request.connect(save_log)


# Access keys
# -----------
if settings.ADREST_ACCESSLOG and 'django.contrib.auth' in settings.INSTALLED_APPS:

    import uuid
    from django.contrib.auth.models import User


    class AccessKey(models.Model):
        """ API key.
        """
        key =  models.CharField(max_length=40, blank=True)
        user = models.ForeignKey(User)
        created = models.DateTimeField(auto_now_add=True)

        def __unicode__(self):
            return u"%s for %s" % (self.key, self.user)

        def save(self, **kwargs):
            self.key = self.key or str(uuid.uuid4()).replace('-', '')
            super(AccessKey, self).save(**kwargs)

    admin.site.register(AccessKey)

    # Auto create key for created user
    def create_api_key(sender, **kwargs):
        if kwargs.get('created') is True:
            AccessKey.objects.create(user=kwargs.get('instance'))

    # Connect create handler to user save event
    models.signals.post_save.connect(create_api_key, sender=User)
