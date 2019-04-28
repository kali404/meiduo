from django.conf.urls import url, include
from django.contrib import admin
from . import views
from django import http

urlpatterns = [
    url(r'^qq/login/$', views.QQurlView.as_view()),
    url(r'^oauth_callback/$', views.QQopenidView.as_view()),
]
