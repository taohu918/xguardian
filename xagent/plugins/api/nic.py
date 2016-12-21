# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import subprocess
from xagent.plugins.api.data_format_convert import data_format_convert


def nicinfo(os_distributor, host_type):
    nic_info = []
    if host_type.lower() != 'docker':
        cmd = "ifconfig -a"
        if os_distributor.lower() == 'centos':
            cmd = "cd /etc/sysconfig/network-scripts && ls ls ifcfg-e*"
        if os_distributor.lower() == 'ubuntu':
            cmd = "cat /etc/network/interfaces | grep auto | grep -vi 'lo' | awk '{print $2}'"

        res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res_data = res.stdout.read()
        nic_list = data_format_convert(res_data).rstrip('\n').split('\n')

        for nic_item in nic_list:
            nic_name = nic_item.split('-')[1]
            data = get_info(nic_name)
            nic_info.append(data)

    else:
        nic_dict = {
            'bonding': '',
            'ip': 'docker',
            'mac': 'docker',
            'mask': 'docker',
            'model': 'docker',
            # 'network': 'docker',
            'name': 'docker',
        }
        nic_info.append({'docker': nic_dict})

    return {'nic': nic_info}


def get_info(nic_item):
    mac = 'unknown'
    ip = 'unknown'
    mask = 'unknown'
    network = 'unknown'

    cmd = "ifconfig %s" % nic_item
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res_data = res.stdout.read()
    res_data = data_format_convert(res_data)

    for line in res_data.split('\n'):
        if not line:
            continue

        if 'HWaddr' in line:
            mac = line.split("HWaddr")[1].strip()

        if 'inet addr' in line:
            ip = line.split("inet addr:")[1].split()[0]
            mask = line.split("Mask:")[1].split()[0]
            network = line.split("Bcast:")[1].split()[0]

    nic_dict = {
        'bonding': '',
        'ip': ip,
        'mac': mac,
        'mask': mask,
        'model': 'unknown',
        # 'network': network,
        'name': nic_item,
    }

    return {nic_item: nic_dict}


if __name__ == '__main__':
    import logging
    import json

    try:
        res = nicinfo('centos', 'py')
        print(json.dumps(res, sort_keys=True, indent=4))
    except Exception as e:
        logging.exception(e)
