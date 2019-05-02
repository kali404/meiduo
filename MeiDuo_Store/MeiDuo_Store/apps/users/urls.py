"""MeiDuo_Store URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^usernames/(?P<username>[A-Za-z0-9_-]{5,20})/count/$', views.UsernameCheckView.as_view()),
    url(r'^usernames/(?P<mobile>1[345789]\d{9})/count/$', views.MobileCheckView.as_view()),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^info/$', views.InfoView.as_view(), name='info'),
    url(r'^emails/$', views.EmailView.as_view(), name='emails'),
    url(r'^addresses/$', views.AddressView.as_view(), name='areas'),
    url(r'^emails/verification/$', views.EmailActiveView.as_view(), name='V_emails'),
    # 新增
    url(r'^addresses/create/$', views.CreateAddressView.as_view(), name='create'),
    # 展示Get
    url(r'^addresses/$', views.AddressView.as_view(), name='create'),
    # 修改 and 删除
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),
    # 默认地址的设置
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.UpdateTitleAddressView.as_view()),

]
