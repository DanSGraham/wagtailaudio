from django.conf.urls import include, url
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext, ungettext

import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail.admin.menu import MenuItem
from wagtail.admin.rich_text import HalloPlugin
from wagtail.admin.search import SearchArea
from wagtail.admin.site_summary import SummaryItem
from wagtail.core import hooks
from wagtailaudio import admin_urls, get_audio_model
from wagtailaudio.forms import GroupAudioPermissionFormSet
from wagtailaudio.permissions import permission_policy

@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^audio/', include(admin_urls, namespace='wagtailaudio')),
    ]


class AudioMenuItem(MenuItem):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_menu_item')
def register_audio_menu_item():
    return AudioMenuItem(
        _('Audio'), reverse('wagtailaudio:index'),
        name='audio', classnames='icon icon-media', order=300
    )


@hooks.register('insert_editor_js')
def editor_js():
    return format_html(
        """
        <script>
            window.chooserUrls.audioChooser = '{0}';
        </script>
        """,
        reverse('wagtailaudio:chooser')
    )


class AudioSummaryItem(SummaryItem):
    order = 200
    template = 'wagtailaudio/homepage/site_summary_audio.html'

    def get_context(self):
        return {
            'total_audio': get_audio_model().objects.count(),
        }

    def is_shown(self):
        return permission_policy.user_has_any_permission(
            self.request.user, ['add', 'change', 'delete']
        )


@hooks.register('construct_homepage_summary_items')
def add_audio_summary_item(request, items):
    items.append(AudioSummaryItem(request))


class AudioSearchArea(SearchArea):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_search_area')
def register_audio_search_area():
    return AudioSearchArea(
        _('Audio'), reverse('wagtailaudio:index'),
        name='audio',
        classnames='icon icon-media',
        order=200)


@hooks.register('register_group_permission_panel')
def register_audio_permissions_panel():
    return GroupAudioPermissionFormSet


@hooks.register('describe_collection_contents')
def describe_collection_docs(collection):
    audio_count = get_audio_model().objects.filter(collection=collection).count()
    if audio_count:
        url = reverse('wagtailaudio:index') + ('?collection_id=%d' % collection.id)
        return {
            'count': audio_count,
            'count_text': ungettext(
                "%(count)s audio",
                "%(count)s audio",
                audio_count
            ) % {'count': audio_count},
            'url': url,
}
