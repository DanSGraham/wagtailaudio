from wagtail.core.permission_policies.collections import CollectionOwnershipPermissionPolicy
from wagtailaudio import get_audio_model
from wagtailaudio.models import Audio

permission_policy = CollectionOwnershipPermissionPolicy(
    get_audio_model(),
    auth_model=Audio,
    owner_field_name='uploaded_by_user'
)
