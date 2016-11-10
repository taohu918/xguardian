# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import platform
import importlib


class Collector(object):
    def __init__(self):
        self.platform = platform.system().lower()

    def run(self):
        """
        :return: the system info from local server
        """
        try:
            module = importlib.import_module('plugins.api.%s' % self.platform)
            cls = getattr(module, 'Main')()  # TODO: how important the parenthese is
            # mth = getattr(cls, 'collect')
            # res = mth()
            res = cls.collect()
            return res

        except Exception as e:
            return e
