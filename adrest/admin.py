""" Add ADRest related models to Django admin.
"""
from django.contrib import admin

from .settings import ADREST_CONFIG
from .models import AccessKey, Access

class AccessAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'identifier',
        'method',
        'status_code',
        'uri',
        'version'
    )
    list_filter = 'method', 'version'
    search_fields = 'uri', 'identifier'
    date_hierarchy = 'created_at'

class AccessKeyAdmin(admin.ModelAdmin):
    list_display = 'key', 'user', 'created'
    search_fields = '=key', '=user'
    raw_id_fields = 'user',

if not ADREST_CONFIG['ABSTRACT_ACCESS_KEY']:
    admin.site.register(AccessKey, AccessKeyAdmin)

if not ADREST_CONFIG['ABSTRACT_ACCESS']:
    admin.site.register(Access, AccessAdmin)
