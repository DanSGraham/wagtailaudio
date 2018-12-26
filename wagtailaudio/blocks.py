from django.utils.functional import cached_property

from wagtail.core.blocks import ChooserBlock


class AudioChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        from wagtailaudio import get_audio_model
        return get_audio_model()

    @cached_property
    def widget(self):
        from wagtailaudio.widgets import AdminAudioChooser
        return AdminAudioChooser

    class Meta:
        icon = "audio"
