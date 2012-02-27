from django.conf import settings as django_settings
from django.contrib import admin
from django.db import models

from adrest import settings
from adrest.signals import api_request_finished


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
            verbose_name_plural = "Access"

        def __unicode__(self):
            return "%s - %s" % (self.status_code, self.uri)

    class AccessAdmin(admin.ModelAdmin):
        list_display = 'status_code', 'uri', 'method', 'identifier', 'created_at', 'version'
        list_filter = 'method', 'version'
        search_fields = 'uri', 'identifier'
        date_hierarchy = 'created_at'
    admin.site.register(Access, AccessAdmin)

    def save_log(sender, response=None, request=None, **resources):

        resource = sender

        if not resource.log:
            return

        Access.objects.create(
            uri = request.path_info,
            method = request.method,
            version = str(resource.api),
            status_code = response.status_code,
            request = '%s\n\n%s' % (str(request.META), str(getattr(request, 'data', ''))),
            identifier = resource.identifier or '',
            response = response.content.decode('utf-8')[:5000],
        )

    api_request_finished.connect(save_log)


# Access keys
# -----------
if 'django.contrib.auth' in django_settings.INSTALLED_APPS:

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

    class AccessKeyAdmin(admin.ModelAdmin):
        list_display = 'key', 'user', 'created'
        search_fields = 'key', 'user'
    admin.site.register(AccessKey, AccessKeyAdmin)

    # Auto create key for created user
    def create_api_key(sender, created=False, instance=None, **kwargs):
        if created and instance:
            AccessKey.objects.create(user=instance)

    # Connect create handler to user save event
    if settings.AUTO_CREATE_ACCESSKEY:
        models.signals.post_save.connect(create_api_key, sender=User)
