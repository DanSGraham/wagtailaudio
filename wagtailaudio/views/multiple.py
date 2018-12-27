from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_headers

from wagtail.admin.utils import PermissionPolicyChecker
from wagtail.core.models import Collection
from wagtailaudio import get_audio_model
from wagtailaudio.fields import ALLOWED_EXTENSIONS
from wagtailaudio.forms import get_audio_form
from wagtailaudio.permissions import permission_policy
from wagtail.search.backends import get_search_backends

permission_checker = PermissionPolicyChecker(permission_policy)


def get_audio_edit_form(AudioModel):
    AudioForm = get_audio_form(AudioModel)

    # Make a new form with the file and focal point fields excluded
    class AudioEditForm(AudioForm):
        class Meta(AudioForm.Meta):
            model = AudioModel
            exclude = (
                'file',
            )

    return AudioEditForm


@permission_checker.require('add')
@vary_on_headers('X-Requested-With')
def add(request):
    Audio = get_audio_model()
    AudioForm = get_audio_form(Audio)

    collections = permission_policy.collections_user_has_permission_for(request.user, 'add')
    if len(collections) > 1:
        collections_to_choose = Collection.order_for_display(collections)
    else:
        # no need to show a collections chooser
        collections_to_choose = None

    if request.method == 'POST':
        if not request.is_ajax():
            return HttpResponseBadRequest("Cannot POST to this view without AJAX")

        if not request.FILES:
            return HttpResponseBadRequest("Must upload a file")

        # Build a form for validation
        form = AudioForm({
            'title': request.FILES['files[]'].name,
            'collection': request.POST.get('collection'),
        }, {
            'file': request.FILES['files[]'],
        }, user=request.user)

        if form.is_valid():
            # Save it
            audio = form.save(commit=False)
            audio.uploaded_by_user = request.user
            audio.file_size = audio.file.size
            audio.file.seek(0)
            audio._set_file_hash(audio.file.read())
            audio.file.seek(0)
            audio.save()

            # Success! Send back an edit form for this audio to the user
            return JsonResponse({
                'success': True,
                'audio_id': int(audio.id),
                'form': render_to_string('wagtailaudio/multiple/edit_form.html', {
                    'audio': audio,
                    'form': get_audio_edit_form(Audio)(
                        instance=audio, prefix='audio-%d' % audio.id, user=request.user
                    ),
                }, request=request),
            })
        else:
            # Validation error
            return JsonResponse({
                'success': False,

                # https://github.com/django/django/blob/stable/1.6.x/django/forms/util.py#L45
                'error_message': '\n'.join(['\n'.join([force_text(i) for i in v]) for k, v in form.errors.items()]),
            })
    else:
        form = AudioForm(user=request.user)

    return render(request, 'wagtailimages/multiple/add.html', {
        'max_filesize': form.fields['file'].max_upload_size,
        'help_text': form.fields['file'].help_text,
        'allowed_extensions': ALLOWED_EXTENSIONS,
        'error_max_file_size': form.fields['file'].error_messages['file_too_large_unknown_size'],
        'error_accepted_file_types': form.fields['file'].error_messages['invalid_audio'],
        'collections': collections_to_choose,
    })


@require_POST
def edit(request, audio_id, callback=None):
    Audio = get_audio_model()
    AudioForm = get_audio_edit_form(Audio)

    audio = get_object_or_404(Audio, id=audio_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', audio):
        raise PermissionDenied

    form = AudioForm(
        request.POST, request.FILES, instance=audio, prefix='audio-' + audio_id, user=request.user
    )

    if form.is_valid():
        form.save()

        # Reindex the audio to make sure all tags are indexed
        for backend in get_search_backends():
            backend.add(audio)

        return JsonResponse({
            'success': True,
            'audio_id': int(audio_id),
        })
    else:
        return JsonResponse({
            'success': False,
            'audio_id': int(audio_id),
            'form': render_to_string('wagtailaudio/multiple/edit_form.html', {
                'audio': audio,
                'form': form,
            }, request=request),
        })


@require_POST
def delete(request, audio_id):
    audio = get_object_or_404(get_audio_model(), id=audio_id)

    if not request.is_ajax():
        return HttpResponseBadRequest("Cannot POST to this view without AJAX")

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', audio):
        raise PermissionDenied

    audio.delete()

    return JsonResponse({
        'success': True,
        'audio_id': int(audio_id),
})
