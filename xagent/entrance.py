# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import os
import sys
import platform
import logging


def add_path():
    if platform.system() == "Windows":
        base_dir = '\\'.join(os.path.abspath(os.path.dirname(__file__)).split('\\')[:-1])
    else:
        base_dir = '/'.join(os.path.abspath(os.path.dirname(__file__)).split('/')[:-1])

    sys.path.append(base_dir)


def main():
    from xagent.coremth import Dominator
    slot = ['report_data', 'collect_data']
    if len(sys.argv) > 1 and sys.argv[1] in slot:
        Dominator.Mercurial(sys.argv[1])

    else:
        print('plz chose one of these para: ')
        print('\t report_data')
        print('\t collect_data')


if __name__ == '__main__':
    try:
        add_path()
        main()
    except Exception as e:
        logging.exception(e)
