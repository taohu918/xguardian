# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

import os

BaseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Params = {
    "server": "127.0.0.1",
    "port": 9000,
    'request_timeout': 30,
    "urls": "/asset/report/",
    'local_asset_id_file': '%s/var/.asset_id' % BaseDir,
    'log_file': '%s/logs/run_log' % BaseDir,

    'kinds': 'physics_machines',
    'auth': {
        'user': 'axe',
        'token': '123abc'
    },
}
