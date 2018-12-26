from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


default_app_config = 'wagtail.images.apps.WagtailAudioAppConfig'


def get_audio_model_string():
    """
    Get the dotted ``app.Model`` name for the image model as a string.
    Useful for developers making Wagtail plugins that need to refer to the
    audio model, such as in foreign keys, but the model itself is not required.
    """
    return getattr(settings, 'WAGTAILAUDIO_AUDIO_MODEL', 'wagtailaudio.Audio')


def get_audio_model():
    """
    Get the audio model from the ``WAGTAILAUDIO_AUDIO_MODEL`` setting.
    Useful for developers making Wagtail plugins that need the audio model.
    Defaults to the standard :class:`~wagtailaudio.models.Audio` model
    if no custom model is defined.
    """
    from django.apps import apps
    model_string = get_audio_model_string()
    try:
        return apps.get_model(model_string)
    except ValueError:
        raise ImproperlyConfigured("WAGTAILAUDIO_AUDIO_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "WAGTAILAUDIO_AUDIO_MODEL refers to model '%s' that has not been installed" % model_string
)
