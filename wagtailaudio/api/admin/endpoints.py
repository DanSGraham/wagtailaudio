from ..v2.endpoints import AudioAPIEndpoint
from .serializers import AdminAudioSerializer


class AudioAdminAPIEndpoint(AudioAPIEndpoint):
    base_serializer_class = AdminAudioSerializer

    body_fields = AudioAPIEndpoint.body_fields + [
        'thumbnail',
    ]

    listing_default_fields = AudioAPIEndpoint.listing_default_fields + [
        'thumbnail',
    ]
