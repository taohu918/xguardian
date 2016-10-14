# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import os
import sys
import json
import plugin_dispatcher
import urllib
import urllib2
from conf import settings
import token_generator


class Mercurial(object):
    def __init__(self, argvs):
        self.argvs = argvs
        self.reality()

    def reality(self):  # 执行自身的方法: collect_data/report_data  .etc
        if self.argvs:
            func = getattr(self, self.argvs)
            func()
        else:
            return 'argv error'

    def xmarks(self):
        pass

    @staticmethod
    def collect_data():
        obj = plugin_dispatcher.Collector()
        asset_data = obj.run()
        asset_data['kinds'] = settings.Params['kinds']
        print('\033[1;33m %s \033[0m' % __file__)
        print(json.dumps(asset_data, indent=4))
        # return asset_data

    def report_data(self):
        obj = plugin_dispatcher.Collector()
        this_asset_data = obj.run()
        this_asset_data['kinds'] = settings.Params['kinds']
        this_asset_data['hosted'] = settings.Params['hosted']

        this_asset_id = self.local_asset_id()
        if this_asset_id:
            this_asset_data["asset_uid"] = this_asset_id
        else:
            this_asset_data["asset_uid"] = 0

        # this_asset_data["model"] = 'l3330'

        # this_asset_data is a large dict, cover all hardware and software info
        data = {"asset_data": json.dumps(this_asset_data)}
        response = self.__submit_asset_data(data, method='post')
        # print(response)

    @staticmethod
    def local_asset_id(sn=None):
        local_asset_id_file = settings.Params['local_asset_id_file']
        if os.path.isfile(local_asset_id_file):
            local_asset_id = file(local_asset_id_file).read().strip()
            return local_asset_id
            # if local_asset_id.isdigit():
            #     return local_asset_id
            # else:
            #     return False
        else:
            return False

    def __submit_asset_data(self, data, method='post'):
        url_base = "http://%s:%s%s" % (settings.Params['server'], settings.Params['port'], settings.Params['urls'])
        url = self.__attach_token_for_url(url_base)

        if method == "post":
            try:
                data_encode = urllib.urlencode(data)
                req = urllib2.Request(url=url, data=data_encode)
                res_data = urllib2.urlopen(req, timeout=settings.Params['request_timeout'])
                callback_msg = res_data.read()
                print('\033[1;33m %s \033[0m' % __file__)
                print type(callback_msg), callback_msg
                self.write_uid_into_file(callback_msg)
            except Exception, e:
                sys.exit("\033[31;1m%s\033[0m" % e)

        elif method == "get":
            args = ""
            for k, v in data.items():
                args += "&%s=%s" % (k, v)
            args = args[1:]

            url_with_asset_data = "%s&%s" % (url, args)

            try:
                req = urllib2.Request(url_with_asset_data)
                req_data = urllib2.urlopen(req, timeout=settings.Params['request_timeout'])
                callback = req_data.read()
                print "-->server response:", type(callable), callback
                return callback
            except urllib2.URLError, e:
                sys.exit("\033[31;1m%s\033[0m" % e)

        return 'msg'

    @staticmethod
    def __attach_token_for_url(url):
        user = settings.Params['auth']['user']
        token = settings.Params['auth']['token']
        tokend, ts = token_generator.gettoken(user, token)

        url_arg = "user=%s&ts=%s&tokend=%s" % (user, ts, tokend)
        if "?" in url:
            new_url = url + "&" + url_arg
        else:
            new_url = url + "?" + url_arg

        return new_url

    def write_uid_into_file(self, asset_uid_from_server):
        asset_uid = json.loads(asset_uid_from_server).get('asset_uid')
        print type(asset_uid), asset_uid
        if asset_uid:
            try:
                local_asset_id_file = settings.Params['local_asset_id_file']
                local_asset_id = file(local_asset_id_file).read().strip()
                if str(asset_uid) != str(local_asset_id):
                    file_obj = open(local_asset_id_file, 'w')
                    file_obj.write(asset_uid)
                    file_obj.close()
            except Exception, e:
                print e
