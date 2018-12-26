from ..fields import AudioRenditionField
from ..v2.serializers import AudioSerializer


class AdminAudioSerializer(AudioSerializer):
    thumbnail = AudioRenditionField('max-165x165', source='*', read_only=True)
