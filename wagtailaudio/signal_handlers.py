from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, pre_save

from wagtailaudio import get_audio_model


def post_delete_file_cleanup(instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    transaction.on_commit(lambda: instance.file.delete(False))


def register_signal_handlers():
    Audio = get_audio_model()

    post_delete.connect(post_delete_file_cleanup, sender=Audio)
