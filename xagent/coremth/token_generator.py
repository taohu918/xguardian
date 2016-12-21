# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

import hashlib
import time


def gettoken(username, token):
    timestamp = int(time.time())
    md5_format_str = "%s@%s:%s" % (username, timestamp, token)
    # print(type(md5_format_str), md5_format_str)
    # exit()
    obj = hashlib.md5()
    obj.update(md5_format_str.encode('utf-8'))
    tokend = obj.hexdigest()

    # print "token format : [%s]" % md5_format_str
    # print "token : [%s]" % tokend
    return tokend[10:17], timestamp


if __name__ == '__main__':
    import logging

    try:
        print(gettoken('axe', 'test'))
    except Exception as e:
        logging.exception(e)
