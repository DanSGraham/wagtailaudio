import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.fields import FileField
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

ALLOWED_EXTENSIONS = ['mp3', 'ogg', 'wav']
SUPPORTED_FORMATS_TEXT = _("MP3, OGG, WAV")


class WagtailAudioField(FileField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get max upload size from settings
        self.max_upload_size = getattr(settings, 'WAGTAILAUDIO_MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
        max_upload_size_text = filesizeformat(self.max_upload_size)

        # Help text
        if self.max_upload_size is not None:
            self.help_text = _(
                "Supported formats: %(supported_formats)s. Maximum filesize: %(max_upload_size)s."
            ) % {
                'supported_formats': SUPPORTED_FORMATS_TEXT,
                'max_upload_size': max_upload_size_text,
            }
        else:
            self.help_text = _(
                "Supported formats: %(supported_formats)s."
            ) % {
                'supported_formats': SUPPORTED_FORMATS_TEXT,
            }

        # Error messages
        self.error_messages['invalid_audio'] = _(
            "Not a supported audio format. Supported formats: %s."
        ) % SUPPORTED_FORMATS_TEXT

        self.error_messages['invalid_audio_known_format'] = _(
            "Not a valid %s audio."
        )

        self.error_messages['file_too_large'] = _(
            "This file is too big (%%s). Maximum filesize %s."
        ) % max_upload_size_text

        self.error_messages['file_too_large_unknown_size'] = _(
            "This file is too big. Maximum filesize %s."
        ) % max_upload_size_text

    def check_audio_file_format(self, f):
        # Check file extension
        extension = os.path.splitext(f.name)[1].lower()[1:]

        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError(self.error_messages['invalid_audio'], code='invalid_audio')

        audio_format = extension.upper()

        #Check internal format using mutagen.
        from mutagen import File
        internal_audio_format = File(f.name)
        if internal_audio_format is None:
            print ("Couldn't find file")
        else:
            in_type = type(internal_audio_format).__name__
            if in_type in ['ID3' or 'MP3']:
                internal_audio_format = 'MP3'
            elif in_type == 'OggVorbis':
                internal_audio_format = 'OGG'
            elif in_type == 'WavPack':
                internal_audio_format = 'WAV'
            else:
                internal_audio_format = "UNSUPPORTED TYPE"

            # Check that the internal format matches the extension
            if internal_audio_format != audio_format:
                raise ValidationError(self.error_messages['invalid_audio_known_format'] % (
                    image_format,
                ), code='invalid_audio_known_format')

    def check_audio_file_size(self, f):
        # Upload size checking can be disabled by setting max upload size to None
        if self.max_upload_size is None:
            return

        # Check the filesize
        if f.size > self.max_upload_size:
            raise ValidationError(self.error_messages['file_too_large'] % (
                filesizeformat(f.size),
            ), code='file_too_large')

    def to_python(self, data):
        f = super().to_python(data)

        if f is not None:
            self.check_audio_file_size(f)
            self.check_audio_file_format(f)

        return f
