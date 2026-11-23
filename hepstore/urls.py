from django.contrib import admin
from django.urls import path, include
urlpatterns = [
 path('admin/', admin.site.urls),
 path('tai-khoan/', include('django.contrib.auth.urls')),
 path('', include('shop.urls')),
]
admin.site.site_header='Hép Bookstore · Quản trị hệ thống'
admin.site.site_title='Hép Bookstore'
admin.site.index_title='Quản trị dữ liệu'
