# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import sys


def data_format_convert(data):
    if sys.version.split('.')[0] == '3':
        data = str(data, encoding='utf-8')
    elif sys.version.split('.')[0] == '2':
        data = str(data)
    return data
