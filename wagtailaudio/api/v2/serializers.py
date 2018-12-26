from rest_framework.fields import Field
from wagtail.api.v2.serializers import BaseSerializer


class AudioDownloadUrlField(Field):
    """
    Serializes the "download_url" field for audio.
    Example:
    "download_url": "/media/audio/a_test_audio.mp3"
    """
    def get_attribute(self, instance):
        return instance

    def to_representation(self, audio):
        return audio.file.url


class AudioSerializer(BaseSerializer):
    download_url = AudioDownloadUrlField(read_only=True)
