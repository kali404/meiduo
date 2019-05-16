from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^carts/$', views.CartsView.as_view()),
    url(r'^carts/selection/$', views.CartsSelectAllView.as_view()),
    url(r'^carts/simple/$', views.CartsSimpleView.as_view()),
]
