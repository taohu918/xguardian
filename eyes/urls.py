# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

from django.conf.urls import url, include
import views

urlpatterns = [
    url(r'index/$', views.index, name='index'),
    url(r'login/', views.login, name='login'),
    url(r'^category/(\d+)/$', views.category, name='category'),
    url(r'^$', views.index, name='index'),
]
