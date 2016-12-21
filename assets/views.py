# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from assets.utilsbox import decorations
from assets.utilsbox.data_handler import Handler
import json
from assets import models
from assets.utilsbox.log import logger
from django.views.generic import View
import logging


def mmth(request):
    obj = models.Server.objects.get(uid='A5F9FBD3D87508C8DB39ED985A81D6C2')
    obj_related = obj.business
    print(obj.admin)
    print(obj.business.name)
    print('')


class ServerReport(APIView):
    @decorations.token_validate
    def post(self, request):
        asset_handler = Handler(request)
        try:
            asset_handler.data_is_valid()
            asset_handler.data_incorporated()
        except Exception as e:
            logging.exception(e)

        if asset_handler.successful:
            msg = json.dumps({'asset_uid': asset_handler.asset_uid})
        else:
            msg = json.dumps({'asset_uid': False})
        print(msg)
        print(asset_handler.asset_uid)
        return HttpResponse(msg)
