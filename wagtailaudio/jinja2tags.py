from jinja2.ext import Extension

from .templatetags.wagtailaudio_tags import audio_url


class WagtailAudioExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)

        self.environment.globals.update({
            'audio_url': audio_url,
        })

# Nicer import names
audio = WagtailAudioExtension
