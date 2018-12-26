import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.admin import messages
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.utils import PermissionPolicyChecker, permission_denied, popular_tags_for_model
from wagtail.core.models import Collection, Site
from wagtailaudio import get_audio_model
from wagtailaudio.exceptions import InvalidFilterSpecError
from wagtailaudio.forms import URLGeneratorForm, get_audio_form
from wagtailaudio.models import Filter, SourceAudioIOError
from wagtailaudio.permissions import permission_policy
from wagtailaudio.views.serve import generate_signature
from wagtail.search import index as search_index
from wagtail.utils.pagination import paginate

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    Audio = get_audio_model()

    # Get audio_files (filtered by user permission)
    audio_files = permission_policy.instances_user_has_any_permission_for(
        request.user, ['change', 'delete']
    ).order_by('-created_at')

    # Search
    query_string = None
    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search audio files"))
        if form.is_valid():
            query_string = form.cleaned_data['q']

            audio_files = audio_files.search(query_string)
    else:
        form = SearchForm(placeholder=_("Search audio files"))

    # Filter by collection
    current_collection = None
    collection_id = request.GET.get('collection_id')
    if collection_id:
        try:
            current_collection = Collection.objects.get(id=collection_id)
            audio_files = audio_files.filter(collection=current_collection)
        except (ValueError, Collection.DoesNotExist):
            pass

    paginator, audio_files = paginate(request, audio_files)

    collections = permission_policy.collections_user_has_any_permission_for(
        request.user, ['add', 'change']
    )
    if len(collections) < 2:
        collections = None
    else:
        collections = Collection.order_for_display(collections)

    # Create response
    if request.is_ajax():
        return render(request, 'wagtailaudio/audio/results.html', {
            'audio_files': audio_files,
            'query_string': query_string,
            'is_searching': bool(query_string),
        })
    else:
        return render(request, 'wagtailaudio/audio/index.html', {
            'audio_files': audio_files,
            'query_string': query_string,
            'is_searching': bool(query_string),

            'search_form': form,
            'popular_tags': popular_tags_for_model(Audio),
            'collections': collections,
            'current_collection': current_collection,
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })


@permission_checker.require('change')
def edit(request, audio_id):
    Audio = get_audio_model()
    AudioForm = get_audio_form(Audio)

    audio = get_object_or_404(Audio, id=audio_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', audio):
        return permission_denied(request)

    if request.method == 'POST':
        original_file = audio.file
        form = AudioForm(request.POST, request.FILES, instance=audio, user=request.user)
        if form.is_valid():
            if 'file' in form.changed_data:
                # Set new image file size
                audio.file_size = audio.file.size

                # Set new image file hash
                audio.file.seek(0)
                audio._set_file_hash(audio.file.read())
                audio.file.seek(0)

            form.save()

            if 'file' in form.changed_data:
                # if providing a new audio file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
                audio.renditions.all().delete()

            # Reindex the audio to make sure all tags are indexed
            search_index.insert_or_update_object(audio)

            messages.success(request, _("Audio '{0}' updated.").format(audio.title), buttons=[
                messages.button(reverse('wagtailaudio:edit', args=(audio.id,)), _('Edit again'))
            ])
            return redirect('wagtailaudio:index')
        else:
            messages.error(request, _("The audio could not be saved due to errors."))
    else:
        form = AudioForm(instance=audio, user=request.user)

    # Check if we should enable the frontend url generator
    try:
        reverse('wagtailaudio_serve', args=('foo', '1', 'bar'))
        url_generator_enabled = True
    except NoReverseMatch:
        url_generator_enabled = False

    if audio.is_stored_locally():
        # Give error if audio file doesn't exist
        if not os.path.isfile(audio.file.path):
            messages.error(request, _(
                "The source audio file could not be found. Please change the source or delete the image."
            ).format(audio.title), buttons=[
                messages.button(reverse('wagtailaudio:delete', args=(audio.id,)), _('Delete'))
            ])

    try:
        filesize = audio.get_file_size()
    except SourceAudioIOError:
        filesize = None

    return render(request, "wagtailaudio/audio/edit.html", {
        'audio': audio,
        'form': form,
        'url_generator_enabled': url_generator_enabled,
        'filesize': filesize,
        'user_can_delete': permission_policy.user_has_permission_for_instance(
            request.user, 'delete', audio
        ),
    })


def url_generator(request, audio_id):
    audio = get_object_or_404(get_audio_model(), id=audio_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', audio):
        return permission_denied(request)

    return render(request, "wagtailaudio/audio/url_generator.html", {
        'image': image,
    })


def generate_url(request, audio_id, filter_spec):
    # Get the audio
    Audio = get_audio_model()
    try:
        Audio = Audio.objects.get(id=audio_id)
    except Audio.DoesNotExist:
        return JsonResponse({
            'error': "Cannot find audio."
        }, status=404)

    # Check if this user has edit permission on this image
    if not permission_policy.user_has_permission_for_instance(request.user, 'change', audio):
        return JsonResponse({
            'error': "You do not have permission to generate a URL for this audio."
        }, status=403)

    # Generate url
    signature = generate_signature(audio_id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, audio_id, filter_spec))

    # Get site root url
    try:
        site_root_url = Site.objects.get(is_default_site=True).root_url
    except Site.DoesNotExist:
        site_root_url = Site.objects.first().root_url

    # Generate preview url
    preview_url = reverse('wagtailaudio:preview', args=(audio_id, filter_spec))

    return JsonResponse({'url': site_root_url + url, 'preview_url': preview_url}, status=200)


def preview(request, audio_id, filter_spec):
    audio = get_object_or_404(get_audio_model(), id=audio_id)

    try:
        response = HttpResponse()
        audio = Filter(spec=filter_spec).run(audio, response)
        response['Content-Type'] = 'audio/' + audio.format_name
        return response
    except InvalidFilterSpecError:
        return HttpResponse("Invalid filter spec: " + filter_spec, content_type='text/plain', status=400)


@permission_checker.require('delete')
def delete(request, audio_id):
    audio = get_object_or_404(get_audio_model(), id=audio_id)

    if not permission_policy.user_has_permission_for_instance(request.user, 'delete', audio):
        return permission_denied(request)

    if request.method == 'POST':
        audio.delete()
        messages.success(request, _("Audio File '{0}' deleted.").format(audio.title))
        return redirect('wagtailaudio:index')

    return render(request, "wagtailaudio/audio/confirm_delete.html", {
        'audio': audio,
    })


@permission_checker.require('add')
def add(request):
    AudioModel = get_audio_model()
    AudioForm = get_audio_form(AudioModel)

    if request.method == 'POST':
        audio = AudioModel(uploaded_by_user=request.user)
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

            messages.success(request, _("Audio file '{0}' added.").format(audio.title), buttons=[
                messages.button(reverse('wagtailaudio:edit', args=(audio.id,)), _('Edit'))
            ])
            return redirect('wagtailaudio:index')
        else:
            messages.error(request, _("The audio could not be created due to errors."))
    else:
        form = AudioForm(user=request.user)

    return render(request, "wagtailaudio/audio/add.html", {
        'form': form,
    })


def usage(request, audio_id):
    audio = get_object_or_404(get_audio_model(), id=audio_id)

    paginator, used_by = paginate(request, audio.get_usage())

    return render(request, "wagtailaudio/audio/usage.html", {
        'audio': audio,
        'used_by': used_by
    })