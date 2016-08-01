# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import platform
import os
import sys

# if platform.system() == "Windows":
#     BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
# # BASE_DIR = '\\'.join(os.path.abspath(os.path.dirname(__file__)).split('\\')[:-1])
# else:
#     BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
#     # BASE_DIR = '/'.join(os.path.abspath(os.path.dirname(__file__)).split('/')[:-1])


BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(BASE_DIR)
# print(BASE_DIR)
# print(sys.path)

if __name__ == '__main__':
    from coremth import Dominator

    try:
        Dominator.Mercurial(sys.argv[1])
    except Exception as e:
        print(e)
