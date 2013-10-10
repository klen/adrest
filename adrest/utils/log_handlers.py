#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.utils.encoding import smart_unicode
from adrest.models import Access


def db_handler(resource, request=None, response=None, **resources):

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


