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

        #TODO: USE MUTAGEN TO VERIFY INTERNAL TYPE, AS WITH WAGTAIL IMAGES.
        #WIll be checked below, but must add the field part as well. See images for examples.
 
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

        #internal_image_format = f.image.format.upper()

        ## Check that the internal format matches the extension
        #if internal_image_format != image_format:
        #    raise ValidationError(self.error_messages['invalid_image_known_format'] % (
        #        image_format,
        #    ), code='invalid_image_known_format')

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