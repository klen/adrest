""" Add ADREST related models to Django admin. """

from django.contrib import admin


try:
    from .models import Access

    class AccessAdmin(admin.ModelAdmin):

        """ Support access log in django admin. """

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

    admin.site.register(Access, AccessAdmin)

except ImportError:
    pass


try:
    from .models import AccessKey

    class AccessKeyAdmin(admin.ModelAdmin):

        """ Support access keys in django admin. """

        list_display = 'key', 'user', 'created'
        search_fields = '=key', '=user'
        raw_id_fields = 'user',

    admin.site.register(AccessKey, AccessKeyAdmin)

except ImportError:
    pass
