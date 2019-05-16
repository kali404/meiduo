from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^areas/$', views.AreaView.as_view(), name='areas'),
    # url(r'^areas/simple/$', views.AreaView.as_view(), name='areas'),
]