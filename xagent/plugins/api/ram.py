# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import subprocess
from xagent.plugins.api.data_format_convert import data_format_convert

cmd_dict = {
    # 'asset_tag_list': "sudo dmidecode -t 17 | grep -i 'Asset Tag' | awk -F':' '{print $2}'",
    'capacity_list': "sudo dmidecode -t 17 | grep -i 'Size' | awk -F':' '{print $2}' | awk -F'MB' '{print $1}'",
    'manufactory_list': "sudo dmidecode -t 17 | grep -i 'Manufacturer' | awk -F':' '{print $2}'",
    'slot_list': "sudo dmidecode -t 17 | grep -i 'DIMM' | grep -vi 'Form Factor' | awk -F':' '{print $2}'",
    'sn_list': "sudo dmidecode -t 17 | grep -i 'Serial Number' | awk -F':' '{print $2}'",
    'type_list': "sudo dmidecode -t 17 | grep -i 'DDR' | awk -F':' '{print $2}'",
}

info_dict = {}  # 存储 list的name 及 list本身 { name: [] }
info_list = []  # 最终返回 {'ram': info_list}


def raminfo(host_type):
    # 计算总内存
    cmd = "cat /proc/meminfo | grep -i MemTotal | awk '{print $2}'"
    s1 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s1_err = s1.stderr.read()
    if s1_err:
        exit(s1_err)

    mem_total_kb = data_format_convert(s1.stdout.read())
    mem_total_mb = int(int(mem_total_kb) / 1024)

    mem_total_gb = int(mem_total_mb) / 1024

    ram_size = '%s GB' % int(mem_total_gb)

    # 统计每个内存条信息
    if host_type == 'physical':
        for k, v in cmd_dict.items():
            res = subprocess.Popen(v, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            res_err = res.stderr.read()
            if res_err:
                exit(res_err)

            res_msg = res.stdout.read()
            res_msg = data_format_convert(res_msg).rstrip("\n")

            general_list(k, res_msg)

        general_dick()

    else:
        info_list.append(
            {'slotx': {
                # 'asset_tag': host_type,
                'capacity': str(mem_total_mb) + ' MB',
                'manufactory': host_type,
                'model': 'Virtual Memory',
                'slot': host_type,
                'sn': host_type,
                'type': host_type,
            }}
        )

    return {'ram': info_list, 'ram_size': ram_size}


def general_list(list_name, list_str):
    # 把字符串转换成列表, 再更新到字典
    tmp_list = []
    for item in list_str.split('\n'):
        if item.strip():
            tmp_list.append(item.strip())
        else:
            tmp_list.append('x')
    info_dict.update({list_name: tmp_list})


def general_dick():
    # 把列表转换成字典
    for item in info_dict['slot_list']:
        itme_index = info_dict['slot_list'].index(item)
        info_list.append(
            {item: {
                # 'asset_tag': info_dict['asset_tag_list'][itme_index],
                'capacity': str(info_dict['capacity_list'][itme_index]) + ' MB',
                'manufactory': info_dict['manufactory_list'][itme_index],
                'model': 'Physical Memory',
                'slot': info_dict['slot_list'][itme_index],
                'sn': info_dict['sn_list'][itme_index],
                'type': info_dict['type_list'][itme_index],
            }}
        )


if __name__ == '__main__':
    import logging
    import json

    try:
        res = raminfo('vm')
        print(json.dumps(res, sort_keys=True, indent=4))
    except Exception as e:
        logging.exception(e)
