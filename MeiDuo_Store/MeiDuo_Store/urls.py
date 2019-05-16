from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('users.urls', namespace='users')),
    url(r'^', include('verifications.urls', namespace='verifications')),
    url(r'^', include('contents.urls', namespace='contents')),
    url(r'^', include('oauth.urls', namespace='oauth')),
    url(r'^', include('areas.urls', namespace='areas')),
    url(r'^', include('goods.urls', namespace='goods')),
    url(r'^', include('carts.urls', namespace='carts')),
    url(r'^', include('orders.urls', namespace='orders')),
    url(r'^search/', include('haystack.urls')),  # 搜索
]
