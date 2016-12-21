# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

# import commands
import subprocess
from xagent.plugins.api.data_format_convert import data_format_convert
from xagent.plugins.api.disk import Disk
from xagent.plugins.api.nic import nicinfo
from xagent.plugins.api.cpu import cpuinfo
from xagent.plugins.api.ram import raminfo


class Main(object):
    def __init__(self):
        self.host_type = None  # 机器类型
        self.docker = False  # 是否为 docker

        self.os_distributor = None  # os 的类型: CentOS/Ubuntu  and so on
        self.os_description = None  # os 描述
        self.os_release = None
        self.os_codename = None
        self.data = {}
        self.hostinfo()

    def collect(self):
        filter_keys = ['Manufacturer', 'Serial Number', 'Product Name', 'UUID', 'Wake-up Type']
        raw_data = {}

        if not self.docker:
            for key in filter_keys:
                res = subprocess.Popen("sudo dmidecode -t system|grep '%s'" % key,
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.stderr.read():
                    exit("linux.py: sudo dmidecode -t system|grep '%s' failed .. " % key)

                res_output = res.stdout.read()
                res_output = data_format_convert(res_output)

                res_validate = res_output.split(':')[1].strip()
                raw_data[key] = res_validate
        else:
            sn = subprocess.Popen("sudo hostname", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            sn_output = data_format_convert(sn.stdout.read()).strip('\n')

            raw_data['UUID'] = sn_output
            raw_data['Serial Number'] = sn_output
            raw_data['Manufacturer'] = 'docker'
            raw_data['Product Name'] = 'docker'
            raw_data['Wake-up Type'] = 'docker'

        self.data.update({
            'uuid': raw_data['UUID'],
            'sn': raw_data['Serial Number'],
            'manufactory': raw_data['Manufacturer'],
            'model': raw_data['Product Name'],
            'wake_up_type': raw_data['Wake-up Type'],
        })

        self.data.update(nicinfo(self.os_distributor, self.host_type))
        self.data.update(cpuinfo())
        self.data.update(raminfo(self.host_type))
        self.data.update(Disk(self.os_distributor, self.host_type).diskinfo())
        return self.data

    def hostinfo(self):
        # 通过 CPU 来判断机器的类型：物理机、虚拟机及其虚拟化技术等
        cpu_v = subprocess.Popen("sudo lscpu | grep Virtualization",
                                 shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cpu_h = subprocess.Popen("sudo lscpu | grep Hypervisor",
                                 shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        cpu_v = data_format_convert(cpu_v.stdout.read())
        cpu_h = data_format_convert(cpu_h.stdout.read())

        if cpu_v.split(':')[1].strip() == 'VT-x':
            self.host_type = 'physical'
        elif cpu_h.split(':')[1]:
            self.host_type = cpu_h.split(':')[1].strip('\n').strip()
        else:
            self.host_type = 'unknown'

        # 判定是否为 docker, docker 无 --privileged 启动, 不能执行一些命令, 故做标记
        docker = subprocess.Popen("df | grep docker",
                                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        docker_output = docker.stdout.read()
        if docker_output:
            self.docker = True
            self.host_type = 'docker'

        if self.docker:
            cmd_check = subprocess.Popen("sudo dpkg -l lsb-core || dudo apt-get install -y lsb-core",
                                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd_check_err = cmd_check.stderr.read()
            if cmd_check_err:
                exit(cmd_check_err)

        # Distributor ID:	CentOS
        distributor = subprocess.Popen("lsb_release -a | grep -i distributor | awk -F':' '{print $2}'",
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.os_distributor = data_format_convert(distributor.stdout.read()).strip().strip('\n')

        # Description:	CentOS release 6.4 (Final)
        description = subprocess.Popen("lsb_release -a | grep -i description | awk -F':' '{print $2}'",
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.os_description = data_format_convert(description.stdout.read()).strip().strip('\n')

        # Release:	6.4
        release = subprocess.Popen("lsb_release -a | grep -i release | awk -F':' '{print $2}'",
                                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.os_release = data_format_convert(release.stdout.read()).strip().strip('\n')

        # Codename:	Final
        codename = subprocess.Popen("lsb_release -a | grep -i codename | awk -F':' '{print $2}'",
                                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.os_codename = data_format_convert(codename.stdout.read()).strip().strip('\n')

        self.data = {
            "os_distributor": self.os_distributor,
            "os_description": self.os_description,
            "os_release": self.os_release,
            "os_codename": self.os_codename,
            "os_classification": "linux",
            "asset_type": 'server',
            "host_type": self.host_type,
        }


if __name__ == "__main__":
    import logging

    try:
        obj = Main()
        res = obj.collect()
        print(res)
    except Exception as e:
        logging.exception(e)
