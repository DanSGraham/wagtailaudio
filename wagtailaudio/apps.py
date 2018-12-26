from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailAudioAppConfig(AppConfig):
    name = 'wagtailaudio'
    label = 'wagtailaudio'
    verbose_name = _("Wagtail audio")

    def ready(self):
        from wagtailaudio.signal_handlers import register_signal_handlers
        register_signal_handlers()
