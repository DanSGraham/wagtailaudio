from django.conf import settings
from django.contrib import admin

from wagtailaudio.models import Audio

if hasattr(settings, 'WAGTAILAUDIO_AUDIO_MODEL') and settings.WAGTAILAUDIO_AUDIO_MODEL != 'wagtailaudio.Audio':
    # This installation provides its own custom audio class;
    # to avoid confusion, we won't expose the unused wagtailaudio.Audio class
    # in the admin.
    pass
else:
    admin.site.register(Audio)
