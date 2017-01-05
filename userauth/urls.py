# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

from django.conf.urls import url, include
from userauth import views

urlpatterns = [
    url(r'changepwd/$', views.changepwd, name='changepwd'),
]
