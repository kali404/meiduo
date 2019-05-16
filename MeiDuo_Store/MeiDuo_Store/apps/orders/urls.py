from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),  #结算页面
    url(r'^orders/commit/$', views.OrderCommitView.as_view()),  #结算页面
    url(r'^orders/success/$', views.SuccessView.as_view()),  #结算页面
    url(r'^orders/info/(?P<page_num>\d+)/$', views.OrderListView.as_view()),
]
