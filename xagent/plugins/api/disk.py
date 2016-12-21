# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import os
import re
import subprocess
from xagent.plugins.api.data_format_convert import data_format_convert


class Disk(object):
    def __init__(self, os_distributor, host_type):
        self.os_distributor = os_distributor
        self.host_type = host_type

        self.grep_pattern = {
            'slot_list': 'Slot Number',
            'model_list': 'Inquiry Data',
            'capacity_list': 'Raw Size',
            'iface_list': 'PD Type'}

        self.tmp_data = None

        self.info_dict = {}  # 存储 list的name 及 list本身 { name: [] }
        self.info_list = []  # 最终返回 {'disk': self.info_list}

    def diskinfo(self):
        script_path = os.path.dirname(os.path.abspath(__file__))
        s1 = subprocess.Popen("chmod +x %s/MegaCli" % script_path,
                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if s1.stderr.read():
            exit("chmod +x %s/MegaCli failed .. " % script_path)

        # 非物理机
        if self.host_type != 'physical':
            s2 = subprocess.Popen("df | sed 1d | awk '{SUM +=$2} END {print SUM}'",
                                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            s2_output = s2.stdout.read()
            unit_mb = 1024
            capacity = int(s2_output) / unit_mb

            vitual_info = {
                'slotx': {
                    'capacity': str(capacity) + ' MB',
                    'iface': self.os_distributor,
                    'manufactory': self.os_distributor,
                    'model': self.os_distributor,
                    'slot': 'slotx',
                }
            }

            self.info_list.append(vitual_info)
            return {'disk': self.info_list}

        # 物理机
        for k, v in self.grep_pattern.items():
            cmd = "sudo %s/MegaCli  -PDList -aALL | grep -i '%s' | awk -F':' '{print $2}'" % (script_path, v)

            self.tmp_data = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if self.tmp_data.stderr.read():
                exit("get %s failed .. " % res)

            self.tmp_data = self.tmp_data.stdout.read()
            self.tmp_data = data_format_convert(self.tmp_data)

            self.general_list(k, self.tmp_data)

        self.general_dick()

        return {'disk': self.info_list}

    def general_dick(self):
        # print(to_be_digit(self.info_dict['capacity_list']))
        self.info_dict['capacity_list'] = to_be_digit(self.info_dict['capacity_list'])

        # 把列表转换成字典
        for item in self.info_dict['slot_list']:
            itme_index = self.info_dict['slot_list'].index(item)
            self.info_list.append(
                {item: {
                    'capacity': str(self.info_dict['capacity_list'][itme_index]) + ' MB',
                    'iface': self.info_dict['iface_list'][itme_index],
                    'manufactory': '',
                    'model': self.info_dict['model_list'][itme_index],
                    'slot': item,
                }}
            )

    def general_list(self, list_name, list_str):
        # 把字符串转换成列表, 再更新到字典
        tmp_list = []
        for item in list_str.split('\n'):
            if item.strip():
                tmp_list.append(item.strip())
        self.info_dict.update({list_name: tmp_list})


def to_be_digit(xlist):
    unit_dict = {
        'mb': 1,
        'gb': 1024,
        'tb': 1024 * 1024
    }

    for index, item in enumerate(xlist):
        print(index, item)
        for k, v in unit_dict.items():
            if re.search(k, item.lower()):
                num = item.lower().split(k)[0].strip()
                print(num)
                xlist[index] = int(float(num) * v)
                break

    return xlist


if __name__ == '__main__':
    import logging
    import json

    try:
        obj = Disk('test', 'test')
        res = obj.diskinfo()
        print(json.dumps(res, indent=4, sort_keys=True))
    except Exception as e:
        logging.exception(e)
