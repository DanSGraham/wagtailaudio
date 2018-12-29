from django import forms
from django.forms.models import modelform_factory
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from wagtail.admin import widgets
from wagtail.admin.forms.collections import (
    BaseCollectionMemberForm, collection_member_permission_formset_factory)
from wagtailaudio.fields import WagtailAudioField
from wagtailaudio.models import Audio
from wagtailaudio.permissions import permission_policy as audio_permission_policy


# Callback to allow us to override the default form field for the audio file field
def formfield_for_dbfield(db_field, **kwargs):
    # Check if this is the file field
    if db_field.name == 'file':
        return WagtailAudioField(label=capfirst(db_field.verbose_name), **kwargs)

    # For all other fields, just call its formfield() method.
    return db_field.formfield(**kwargs)


class BaseAudioForm(BaseCollectionMemberForm):
    permission_policy = audio_permission_policy


def get_audio_form(model):
    fields = model.admin_form_fields
    if 'collection' not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ['collection']

    return modelform_factory(
        model,
        form=BaseAudioForm,
        fields=fields,
        formfield_callback=formfield_for_dbfield,
        # set the 'file' widget to a FileInput rather than the default ClearableFileInput
        # so that when editing, we don't get the 'currently: ...' banner which is
        # a bit pointless here
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput(),
            'thumbnail': forms.ClearableFileInput(),
        })


GroupAudioPermissionFormSet = collection_member_permission_formset_factory(
    Audio,
    [
        ('add_audio', _("Add"), _("Add/edit audio you own")),
        ('change_audio', _("Edit"), _("Edit any audio")),
    ],
    'wagtailaudio/permissions/includes/audio_permissions_formset.html'
)
