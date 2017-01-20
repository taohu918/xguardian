# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

from django.conf.urls import url
from userauth import views

urlpatterns = [
    url(r'changepwd/$', views.changepwd, name='changepwd'),
    url(r'account/data/$', views.account_data, name='account_data'),
    url(r'row_data_save/$', views.row_data_save, name='row_data_save'),
]
