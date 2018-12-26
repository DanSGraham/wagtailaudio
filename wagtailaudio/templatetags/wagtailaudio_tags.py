import re

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch
from django.utils.functional import cached_property

from wagtailaudio.views.serve import generate_audio_url


@register.simple_tag()
def audio_url(image, filter_spec, viewname='wagtailaudio_serve'):
    try:
        return generate_audio_url(audio, filter_spec, viewname)
    except NoReverseMatch:
        raise ImproperlyConfigured(
            "'audio_url' tag requires the " + viewname + " view to be configured. Please see "
            "https://docs.wagtail.io/en/stable/advanced_topics/audio/audio_serve_view.html#setup for instructions."
    )
