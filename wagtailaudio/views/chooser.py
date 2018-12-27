from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import ugettext as _

from wagtail.admin.forms.search import SearchForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.utils import PermissionPolicyChecker, popular_tags_for_model
from wagtail.core import hooks
from wagtail.core.models import Collection
from wagtailaudio import get_audio_model
from wagtailaudio.forms import get_audio_form
from wagtailaudio.permissions import permission_policy
from wagtail.search import index as search_index
from wagtail.utils.pagination import paginate

permission_checker = PermissionPolicyChecker(permission_policy)


def get_chooser_js_data():
    """construct context variables needed by the chooser JS"""
    return {
        'step': 'chooser',
        'error_label': _("Server Error"),
        'error_message': _("Report this error to your webmaster with the following information:"),
        'tag_autocomplete_url': reverse('wagtailadmin_tag_autocomplete'),
    }


def get_audio_result_data(audio):
    """
    helper function: given an audio file, return the json data to pass back to the
    audio chooser panel
    """
    return {
        'id': audio.id,
        'edit_link': reverse('wagtailaudio:edit', args=(audio.id,)),
        'title': audio.title,
    }


def get_chooser_context(request):
    """Helper function to return common template context variables for the main chooser view"""

    collections = Collection.objects.all()
    if len(collections) < 2:
        collections = None
    else:
        collections = Collection.order_for_display(collections)

    return {
        'searchform': SearchForm(),
        'is_searching': False,
        'query_string': None,
        'collections': collections,
    }


def chooser(request):
    Audio = get_audio_model()

    if permission_policy.user_has_permission(request.user, 'add'):
        AudioForm = get_audio_form(Audio)
        uploadform = AudioForm(user=request.user)
    else:
        uploadform = None

    audio_files = Audio.objects.order_by('-created_at')

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_image_chooser_queryset'):
        audio_files = hook(audio_files, request)

    if (
        'q' in request.GET or 'p' in request.GET or 'tag' in request.GET
        or 'collection_id' in request.GET
    ):
        # this request is triggered from search, pagination or 'popular tags';
        # we will just render the results.html fragment
        collection_id = request.GET.get('collection_id')
        if collection_id:
            audio_files = audio_files.filter(collection=collection_id)

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            audio_files = audio_files.search(q)
            is_searching = True
        else:
            is_searching = False
            q = None

            tag_name = request.GET.get('tag')
            if tag_name:
                audio_files = audio_files.filter(tags__name=tag_name)

        # Pagination
        paginator, audio_files = paginate(request, audio_files, per_page=12)

        return render(request, "wagtailimages/chooser/results.html", {
            'audio_files': audio_files,
            'is_searching': is_searching,
            'query_string': q,
        })
    else:
        paginator, audio_files = paginate(request, audio_files, per_page=12)

        context = get_chooser_context(request)
        context.update({
            'audio_files': audio_files,
            'uploadform': uploadform,
        })
        return render_modal_workflow(
            request, 'wagtailimages/chooser/chooser.html', None, context,
            json_data=get_chooser_js_data()
        )


def audio_chosen(request, audio_id):
    audio = get_object_or_404(get_audio_model(), id=audio_id)

    return render_modal_workflow(
        request, None, None,
        None, json_data={'step': 'audio_chosen', 'result': get_audio_result_data(audio)}
    )


@permission_checker.require('add')
def chooser_upload(request):
    Audio = get_audio_model()
    AudioForm = get_audio_form(Audio)

    if request.method == 'POST':
        audio = Audio(uploaded_by_user=request.user)
        form = AudioForm(request.POST, request.FILES, instance=audio, user=request.user)

        if form.is_valid():
            # Set image file size
            audio.file_size = audio.file.size

            # Set image file hash
            audio.file.seek(0)
            audio._set_file_hash(audio.file.read())
            audio.file.seek(0)

            form.save()

            # Reindex the image to make sure all tags are indexed
            search_index.insert_or_update_object(audio)

            return render_modal_workflow(
                request, None, None,
                None, json_data={'step': 'audio_chosen', 'result': get_audio_result_data(audio)}
                )
    else:
        form = AudioForm(user=request.user)

    audio_files = Audio.objects.order_by('-created_at')

    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_audio_chooser_queryset'):
        audio_files = hook(audio_files, request)

    paginator, audio_files = paginate(request, audio_files, per_page=12)

    context = get_chooser_context(request)
    context.update({
        'audio_files': audio_files,
        'uploadform': form,
    })
    return render_modal_workflow(
        request, 'wagtailaudio/chooser/chooser.html', None, context,
        json_data=get_chooser_js_data()
    )
