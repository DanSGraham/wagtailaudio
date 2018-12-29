import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.widgets import AdminChooser
from wagtailaudio import get_audio_model


class AdminAudioChooser(AdminChooser):
    choose_one_text = _('Choose an audio file')
    choose_another_text = _('Change audio')
    link_to_chosen_text = _('Edit this audio file')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio_model = get_audio_model()

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(self.audio_model, value)
        original_field_html = super().render_html(name, value, attrs)

        return render_to_string("wagtailaudio/widgets/audio_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'audio': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createAudioChooser({0});".format(json.dumps(id_))

    class Media:
        js = [
            'wagtailaudio/js/audio-chooser-modal.js',
            'wagtailaudio/js/audio-chooser.js',
]
