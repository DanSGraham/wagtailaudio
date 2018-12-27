from django.template.loader import render_to_string
from wagtail.admin.edit_handlers import BaseChooserPanel

from .widgets import AdminAudioChooser


class AudioChooserPanel(BaseChooserPanel):
    object_type_name = "audio"

    def widget_overrides(self):
        return {self.field_name: AdminAudioChooser}
