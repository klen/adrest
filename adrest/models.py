""" ADREST related models. """

from django.db import models
from django.utils.encoding import smart_unicode

from . import settings
from .signals import api_request_finished


# Preloads ADREST tags
try:
    from django.template.base import builtins
    from .templatetags import register

    builtins.append(register)

except ImportError:
    pass


# Access log
# -----------
if settings.ADREST_ACCESS_LOG:

    class Access(models.Model):

        """ Log api queries. """

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
            return "#{0} {1}:{2}:{3}".format(
                self.pk, self.method, self.status_code, self.uri)

    def save_log(sender, response=None, request=None, **resources):
        """ Save log to db. """
        resource = sender

        if not resource._meta.log:
            return

        try:
            content = smart_unicode(response.content)[:5000]
        except (UnicodeDecodeError, UnicodeEncodeError):
            if response and response['Content-Type'].lower() not in \
                    [emitter.media_type.lower()
                     for emitter in resource.emitters]:
                content = 'Invalid response content encoding'
            else:
                content = response.content[:5000]

        Access.objects.create(
            uri=request.path_info,
            method=request.method,
            version=str(resource.api or ''),
            status_code=response.status_code,
            request='%s\n\n%s' % (str(request.META), str(
                getattr(request, 'data', ''))),
            identifier=resource.identifier or request.META.get(
                'REMOTE_ADDR', 'anonymous'),
            response=content)

    api_request_finished.connect(save_log)


# Access keys
# -----------
if settings.ADREST_ACCESSKEY:

    import uuid
    from django.conf import settings as django_settings

    class AccessKey(models.Model):

        """ API key. """

        key = models.CharField(max_length=40, blank=True)
        user = models.ForeignKey(django_settings.AUTH_USER_MODEL)
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
        """ Create key for user. """
        if created and instance:
            AccessKey.objects.create(user=instance)

    # Connect create handler to user save event
    if settings.ADREST_AUTO_CREATE_ACCESSKEY:
        from django import VERSION

        user_model = django_settings.AUTH_USER_MODEL
        if VERSION < (1, 7):
            from django.contrib.auth import get_user_model
            user_model = get_user_model()

        models.signals.post_save.connect(create_api_key, sender=user_model)


# pylama:ignore=E1002
