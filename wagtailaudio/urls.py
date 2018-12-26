from django.conf.urls import url

from wagtailaudio.views.serve import serve

urlpatterns = [
    url(r'^([^/]*)/(\d*)/([^/]*)/[^/]*$', serve, name='wagtailaudio_serve'),
]
