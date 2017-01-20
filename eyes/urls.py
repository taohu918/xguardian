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
    # 资产管理
    url(r'assets/$', views.assets, name='assets'),
    url(r'details/(.+)/$', views.details, name='details'),  # 加上(), 传入 views 时当做第二参数, 否则视为 url 的字符串
    url(r'idcinfo/$', views.net_res, name='idcinfo'),
    url(r'get_idc_list/$', views.get_idc_list),
    url(r'get_idc_bw/$', views.get_idc_bw),
    url(r'lotupload/$', views.lotupload, name='lotupload'),
    # 服务管理
    url(r'batch/$', views.batch, name='batch'),
    url(r'post_cmds/$', views.post_cmds, name='post_cmd'),
    url(r'get_cmds_res/$', views.get_cmds_res, name='get_cmds_res'),
    url(r'file_distribution/$', views.file_distribution, name='file_distribution'),
    url(r'get_distribution_res/$', views.get_distribution_res, name='get_distribution_res'),
    # 用户管理
    url(r'account_manage/', views.account_manage, name='account_manage'),
    # 变更记录
    url(r'modifylog/$', views.modifylog, name='modifylog'),
    url(r'^$', views.index, name='index'),
]
