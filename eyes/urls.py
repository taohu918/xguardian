# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

from django.conf.urls import url, include
from eyes import views

urlpatterns = [
    url(r'index/$', views.index, name='index'),
    url(r'login/$', views.account_login, name='login'),
    url(r'logout/$', views.account_logout, name='logout'),
    url(r'assets/$', views.assets, name='assets'),
    url(r'details/(.+)/$', views.details),  # TODO: 加上()，传入 views 时当做第二参数。否则视为 url 的字符串
    url(r'modifylog/$', views.modifylog, name='modifylog'),
    url(r'^$', views.index, name='index'),
]
