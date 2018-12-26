from wagtail.api.v2.endpoints import BaseAPIEndpoint
from wagtail.api.v2.filters import FieldsFilter, OrderingFilter, SearchFilter

from ... import get_image_model
from .serializers import AudioSerializer


class AudioAPIEndpoint(BaseAPIEndpoint):
    base_serializer_class = AudioSerializer
    filter_backends = [FieldsFilter, OrderingFilter, SearchFilter]
    body_fields = BaseAPIEndpoint.body_fields + ['title']
    meta_fields = BaseAPIEndpoint.meta_fields + ['tags', 'download_url']
    listing_default_fields = BaseAPIEndpoint.listing_default_fields + ['title', 'tags', 'download_url']
    nested_default_fields = BaseAPIEndpoint.nested_default_fields + ['title', 'download_url']
    name = 'audio'
    model = get_audio_model()
