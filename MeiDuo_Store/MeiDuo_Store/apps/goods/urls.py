from django.conf.urls import url, include
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view()),
    url(r'^hot/(?P<category_id>\d+)/$', views.HotView.as_view()),
    url(r'^detail/(?P<sku_id>\d+)/$', views.DetalView.as_view()),
    url(r'^detail/visit/(?P<category_id>\d+)/$', views.DetaVisitView.as_view()),
    url(r'^browse_histories/$', views.HistoryView.as_view()),
]
