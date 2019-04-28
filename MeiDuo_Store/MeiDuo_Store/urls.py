from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('users.urls', namespace='users')),
    url(r'^', include('verifications.urls', namespace='verifications')),
    url(r'^', include('contents.urls', namespace='contents')),
    url(r'^', include('oauth.urls', namespace='oauth')),
]
