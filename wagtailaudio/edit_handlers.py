from django.template.loader import render_to_string

from wagtail.admin.compare import ForeignObjectComparison
from wagtail.admin.edit_handlers import BaseChooserPanel

from .widgets import AdminAudioChooser


class AudioChooserPanel(BaseChooserPanel):
    object_type_name = "audio"

    def widget_overrides(self):
        return {self.field_name: AdminAudioChooser}

    def get_comparison_class(self):
        return AudioFieldComparison


class AudioFieldComparison(ForeignObjectComparison):
    def htmldiff(self):
        audio_a, audio_b = self.get_objects()

        return render_to_string("wagtailaudio/widgets/compare.html", {
            'audio_a': audio_a,
            'audio_b': audio_b,
        })


