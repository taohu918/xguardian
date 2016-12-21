# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import subprocess
from xagent.plugins.api.data_format_convert import data_format_convert


def cpuinfo():
    s0 = subprocess.Popen("lscpu && cat /proc/cpuinfo",
                          shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s0_err = s0.stderr.read()
    if s0_err:
        exit(s0_err)

    # centos6 lscpu don't has key 'model name', so use cat /proc/cpuinfo here ..
    s1 = subprocess.Popen("cat /proc/cpuinfo | grep -i 'model name' | uniq | awk -F':' '{print $2}'",
                          shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cpu_model = data_format_convert(s1.stdout.read()).strip().strip().strip('\n')  # CPU型号

    s2 = subprocess.Popen("lscpu | grep -i Socket | grep -vi Core | awk '{print $2}'",
                          shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cpu_socket = data_format_convert(s2.stdout.read())  # CPU物理颗数

    s3 = subprocess.Popen("lscpu | grep -i core | grep -vi thread | awk -F':' '{print $2}' | awk '{print $1}'",
                          shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cpu_cores = data_format_convert(s3.stdout.read())  # 核心数/每颗

    s4 = subprocess.Popen("cat /proc/cpuinfo | grep 'processor' | wc -l",
                          shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cpu_processors = data_format_convert(s4.stdout.read())  # 逻辑个数

    raw_data = {
        'cpu_model': cpu_model,
        'cpu_socket': int(cpu_socket),
        'cpu_cores': int(cpu_cores) * int(cpu_socket),
        'cpu_processors': int(cpu_processors),
        # 'physical_count': "cat /proc/cpuinfo | grep 'physical id' | sort | uniq | wc -l",
        # 'logic_count': "cat /proc/cpuinfo |grep  'processor'|wc -l ",
    }

    # for k, cmd in raw_data.items():
    #     raw_data[k] = commands.getoutput(cmd).strip()

    return raw_data


if __name__ == '__main__':
    import logging

    try:
        res = cpuinfo()
        print(res)
    except Exception as e:
        logging.exception(e)
