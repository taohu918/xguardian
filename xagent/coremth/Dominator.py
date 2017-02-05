# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import os
import sys
import json

from xagent.coremth import plugin_dispatcher
from xagent.coremth import token_generator
from xagent.conf import settings

tag = """
已通过测试:
Centos6: 物理机、VMware、docker
Centos7: 物理机、VMware
Ubuntu14.04: docker
"""


class Mercurial(object):
    def __init__(self, argvs):
        self.url_base = "http://%s:%s%s" % (settings.Params['server'], settings.Params['port'], settings.Params['urls'])
        self.argvs = argvs
        self.reality()

    def reality(self):
        """ 根据传入参数, 通过反射执行对应的方法 """
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
        print(tag)
        print('\033[1;33m %s \033[0m' % __file__)
        print(json.dumps(asset_data, indent=4, sort_keys=True))

    def report_data(self):
        obj = plugin_dispatcher.Collector()
        this_asset_data = obj.run()
        this_asset_data['hosted'] = settings.Params['hosted']
        # this_asset_data['manufactory'] = 1 # 测试用

        this_asset_id = self.local_asset_id()
        if this_asset_id:
            this_asset_data["asset_uid"] = this_asset_id
        else:
            this_asset_data["asset_uid"] = 0

        # this_asset_data is a large dict
        # print(json.dumps(this_asset_data, sort_keys=True, indent=4))
        data = {"asset_data": json.dumps(this_asset_data)}

        response = self.post_asset_data(data)
        self.write_uid_into_file(response)

    @staticmethod
    def local_asset_id(sn=None):
        local_asset_id_file = settings.Params['local_asset_id_file']
        if os.path.isfile(local_asset_id_file):
            local_asset_id = open(local_asset_id_file).read().strip()
            return local_asset_id
        else:
            return False

    def post_asset_data(self, data):
        if sys.version.split('.')[0] == '3':
            import urllib.request
            import urllib.parse

            url = self.__attach_token_for_url(self.url_base)
            data = urllib.parse.urlencode(data)
            data = data.encode('utf-8')
            request = urllib.request.Request(url=url)
            request.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
            f = urllib.request.urlopen(request, data)
            callback_msg = f.read().decode('utf-8')
            # print(callback_msg)
            return callback_msg

        elif sys.version.split('.')[0] == '2':
            import urllib
            import urllib2

            url = self.__attach_token_for_url(self.url_base)
            data_encode = urllib.urlencode(data)
            req = urllib2.Request(url=url, data=data_encode)
            res_data = urllib2.urlopen(req, timeout=settings.Params['request_timeout'])
            callback_msg = res_data.read()
            # print('\033[1;33m %s \033[0m' % __file__, type(callback_msg), callback_msg)
            return callback_msg

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

    @staticmethod
    def write_uid_into_file(asset_uid_from_server):
        asset_uid = json.loads(asset_uid_from_server).get('asset_uid')
        print(type(asset_uid), asset_uid)

        if asset_uid:
            local_asset_id_file = settings.Params['local_asset_id_file']
            local_asset_id = open(local_asset_id_file).read().strip()
            if str(asset_uid) != str(local_asset_id):
                file_obj = open(local_asset_id_file, 'w')
                file_obj.write(asset_uid)
                file_obj.close()

                print('asset_uid has been written into file .asset_id .. ')


if __name__ == '__main__':
    import logging


    def post_asset_data_py3():
        import urllib.request
        import urllib.parse
        url = 'http://127.0.0.1:8000/test/'
        data = urllib.parse.urlencode({'a': 'b'})
        data = data.encode('utf-8')
        request = urllib.request.Request(url=url)
        request.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
        f = urllib.request.urlopen(request, data)
        print(f.read().decode('utf-8'), f.status, f.reason)


    try:
        post_asset_data_py3()
    except Exception as e:
        logging.exception(e)
