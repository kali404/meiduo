
from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url('^payment/(?P<order_id>\d+)/$', views.AlipayUrlView.as_view()),
    url('^payment/status/$', views.AlipayVerifyView.as_view()),
]


