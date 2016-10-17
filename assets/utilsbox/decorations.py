# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
from xguardian import settings
from django.shortcuts import HttpResponse
import json
import hashlib
import time


def tokend_generator(user, ts, tokend):
    md5_format_str = "%s@%s:%s" % (user, ts, tokend)
    obj = hashlib.md5()
    obj.update(md5_format_str)
    return obj.hexdigest()[10:17]


def token_validate(func):
    def wrapper(*args, **kwargs):
        response = {"errors": []}

        params = args[1].GET  # args[1] -> request
        user = params.get('user', None)
        tokend_from_client = params.get('tokend', None)
        ts = params.get('ts', None)
        if not user or not tokend_from_client or not ts:
            response['errors'].append({"auth_failed": "This api requires token authentication!"})
            return HttpResponse(json.dumps(response))

        try:
            tokend_from_server = tokend_generator('axe', ts, '123abc')
            if tokend_from_client == tokend_from_server:
                if abs(time.time() - int(ts)) > settings.TOKEN_TIMEOUT:
                    response['errors'].append({"auth_failed": "The token is expired!"})
                else:
                    pass
            else:
                response['errors'].append({"auth_failed": "Invalid username or token_id"})
        except Exception as e:
            print(e)
            response['errors'].append({"auth_failed": "Invalid username or token_id"})

        if response['errors']:
            return HttpResponse(json.dumps(response))
        else:
            return func(*args, **kwargs)

    return wrapper
