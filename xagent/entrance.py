# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import sys
import logging
from coremth import Dominator


def main():
    slot = ['report_data', 'collect_data']
    if len(sys.argv) > 1 and sys.argv[1] in slot:
        try:
            Dominator.Mercurial(sys.argv[1])
        except Exception as e:
            print(e)
    else:
        print('plz chose one of these para: ')
        print('\t report_data')
        print('\t collect_data')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(e)
