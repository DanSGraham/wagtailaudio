from django.conf.urls import url

from wagtailaudio.views import chooser, audio, multiple

app_name = 'wagtailaudio'
urlpatterns = [
    url(r'^$', audio.index, name='index'),
    url(r'^(\d+)/$', audio.edit, name='edit'),
    url(r'^(\d+)/delete/$', audio.delete, name='delete'),
    url(r'^add/$', audio.add, name='add'),
    url(r'^usage/(\d+)/$', audio.usage, name='audio_usage'),

    url(r'^multiple/add/$', multiple.add, name='add_multiple'),
    url(r'^multiple/(\d+)/$', multiple.edit, name='edit_multiple'),
    url(r'^multiple/(\d+)/delete/$', multiple.delete, name='delete_multiple'),

    url(r'^chooser/$', chooser.chooser, name='chooser'),
    url(r'^chooser/(\d+)/$', chooser.audio_chosen, name='audio_chosen'),
    url(r'^chooser/upload/$', chooser.chooser_upload, name='chooser_upload'),
]
