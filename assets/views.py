# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from utilsbox import decorations
from utilsbox.data_handler import Handler
import json


class ServerReport(APIView):
    @decorations.token_validate
    def post(self, request):
        # print(self.request) # 逆推
        asset_handler = Handler(request)
        asset_handler.data_is_valid()
        asset_handler.data_incorporated()
        if asset_handler.add_successful:
            msg = json.dumps({'asset_uid': asset_handler.asset_uid})
        else:
            msg = json.dumps({'asset_uid': False})
        return HttpResponse(msg)

    def get(self, request):
        pa = request.get_full_path()
        return HttpResponse(pa)
