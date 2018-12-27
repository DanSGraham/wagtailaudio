import hashlib
import os.path
from collections import OrderedDict
from contextlib import contextmanager
from io import BytesIO

from django.conf import settings
from django.core import checks
from django.core.files import File
from django.db import models
from django.forms.utils import flatatt
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from taggit.managers import TaggableManager
from unidecode import unidecode

from wagtail.admin.utils import get_object_usage
from wagtail.core import hooks
from wagtail.core.models import CollectionMember
from wagtail.search import index
from wagtail.search.queryset import SearchableQuerySetMixin


class SourceAudioIOError(IOError):
    """
    Custom exception to distinguish IOErrors that were thrown while opening the source image
    """
    pass


class AudioQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


def get_upload_to(instance, filename):
    """
    Obtain a valid upload path for an audio file.
    This needs to be a module-level function so that it can be referenced within migrations,
    but simply delegates to the `get_upload_to` method of the instance, so that AbstractAudio
    subclasses can override it.
    """
    return instance.get_upload_to(filename)


class AbstractAudio(CollectionMember, index.Indexed, models.Model):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    file = models.FileField(
        verbose_name=_('file'), upload_to=get_upload_to
    )
    duration=models.PositiveIntegerField(verbose_name=_('duration'), null=True, editable=False) #Will be determined using the MUTAGEN library.
    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True, db_index=True)
    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('uploaded by user'),
        null=True, blank=True, editable=False, on_delete=models.SET_NULL
    )

    tags = TaggableManager(help_text=None, blank=True, verbose_name=_('tags'))

    file_size = models.PositiveIntegerField(null=True, editable=False)
    # A SHA-1 hash of the file contents
    file_hash = models.CharField(max_length=40, blank=True, editable=False)

    objects = AudioQuerySet.as_manager()

    def is_stored_locally(self):
        """
        Returns True if the audio is hosted on the local filesystem
        """
        try:
            self.file.path

            return True
        except NotImplementedError:
            return False

    def get_audio_duration(self):
        if self.duration is None:
            try:
                from mutagen import File
                temp_audio = File(self.file.path)
                self.duration = temp_audio.info.length
            except Exception as e:
                raise Exception(str(e))

            self.save(update_fields=['duration'])
        return self.duration
            

    def get_file_size(self):
        if self.file_size is None:
            try:
                self.file_size = self.file.size
            except Exception as e:
                # File not found
                #
                # Have to catch everything, because the exception
                # depends on the file subclass, and therefore the
                # storage being used.
                raise SourceImageIOError(str(e))

            self.save(update_fields=['file_size'])

        return self.file_size

    def _set_file_hash(self, file_contents):
        self.file_hash = hashlib.sha1(file_contents).hexdigest()

    def get_file_hash(self):
        if self.file_hash == '':
            with self.open_file() as f:
                self._set_file_hash(f.read())

            self.save(update_fields=['file_hash'])

        return self.file_hash

    def get_upload_to(self, filename):
        folder_name = 'audio'
        filename = self.file.field.storage.get_valid_name(filename)

        # do a unidecode in the filename and then
        # replace non-ascii characters in filename with _ , to sidestep issues with filesystem encoding
        filename = "".join((i if ord(i) < 128 else '_') for i in unidecode(filename))

        # Truncate filename so it fits in the 100 character limit
        # https://code.djangoproject.com/ticket/9893
        full_path = os.path.join(folder_name, filename)
        if len(full_path) >= 95:
            chars_to_trim = len(full_path) - 94
            prefix, extension = os.path.splitext(filename)
            filename = prefix[:-chars_to_trim] + extension
            full_path = os.path.join(folder_name, filename)

        return full_path

    def get_usage(self):
        return get_object_usage(self)

    @property
    def usage_url(self):
        return reverse('wagtailaudio:audio_usage',
                       args=(self.id,))

    search_fields = CollectionMember.search_fields + [
        index.SearchField('title', partial_match=True, boost=10),
        index.AutocompleteField('title'),
        index.FilterField('title'),
        index.RelatedFields('tags', [
            index.SearchField('name', partial_match=True, boost=10),
            index.AutocompleteField('name'),
        ]),
        index.FilterField('uploaded_by_user'),
    ]

    def __str__(self):
        return self.title

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def thumbnail_filename(self):
        return os.path.basename(self.thumbnail.name)

    @contextmanager
    def open_file(self):
        # Open file if it is closed
        close_file = False
        try:
            audio_file = self.file

            if self.file.closed:
                # Reopen the file
                if self.is_stored_locally():
                    self.file.open('rb')
                else:
                    # Some external storage backends don't allow reopening
                    # the file. Get a fresh file instance. #1397
                    storage = self._meta.get_field('file').storage
                    audio_file = storage.open(self.file.name, 'rb')

                close_file = True
        except IOError as e:
            # re-throw this as a SourceAudioIOError so that calling code can distinguish
            # these from IOErrors elsewhere in the process
            raise SourceAudioIOError(str(e))

        # Seek to beginning
        audio_file.seek(0)

        try:
            yield audio_file
        finally:
            if close_file:
                audio_file.close()


    def is_editable_by_user(self, user):
        from wagtailaudio.permissions import permission_policy
        return permission_policy.user_has_permission_for_instance(user, 'change', self)

    class Meta:
        abstract = True


class Audio(AbstractAudio):
    admin_form_fields = (
        'title',
        'file',
        'collection',
        'thumbnail',
        'tags',
    )

    class Meta:
        verbose_name = _('audio')
        verbose_name_plural = _('audio')

