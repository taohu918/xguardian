# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

from django.conf.urls import url, include
import views

urlpatterns = [
    url(r'index/$', views.index, name='index'),
    url(r'login/$', views.account_login, name='login'),
    url(r'logout/$', views.account_logout, name='logout'),
    url(r'assets/$', views.assets),
    url(r'^$', views.index, name='index'),
]
