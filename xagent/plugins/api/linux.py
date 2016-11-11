# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

import os
import sys
import commands
import re
import subprocess


def data_format_convert(data):
    if sys.version.split('.')[0] == '3':
        data = str(data, encoding='utf-8')
    elif sys.version.split('.')[0] == '2':
        data = str(data)
    return data


class DiskPlugin(object):
    grep_pattern = {'Slot': 'slot', 'Raw Size': 'capacity', 'Inquiry': 'model', 'PD Type': 'iface_type'}

    def diskinfo(self):
        result = {'physical_diskinfo_driver': []}
        script_path = os.path.dirname(os.path.abspath(__file__))

        s1 = subprocess.Popen("chmod +x %s/MegaCli" % script_path,
                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if s1.stderr.read():
            exit("chmod +x %s/MegaCli failed .. " % script_path)

        s2 = subprocess.Popen("sudo %s/MegaCli  -PDList -aALL" % script_path,
                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if s2.stderr.read():
            exit("sudo %s/MegaCli  -PDList -aALL failed .. " % script_path)

        s2_output = s2.stdout.read()
        s2_output = data_format_convert(s2_output)

        result['physical_diskinfo_driver'] = self.parse(s2_output)

        return result

    def parse(self, content):
        # 重构数据结构: 对获取的 diskinfo 数据进行重构
        response = []
        result = []

        # 对字符串进行分段, result 临时列表
        for row_line in content.split("\n\n\n\n"):
            result.append(row_line)

        for item in result:
            temp_dict = {}
            for row in item.split('\n'):
                if not row.strip():
                    continue
                if len(row.split(':')) != 2:
                    continue
                key, value = row.split(':')
                name = self.mega_patter_match(key)
                if name:
                    if key == 'Raw Size':
                        raw_size = re.search('(\d+\.\d+)', value.strip())
                        if raw_size:

                            temp_dict[name] = raw_size.group()
                        else:
                            raw_size = '0'
                    else:
                        temp_dict[name] = value.strip()

            if temp_dict:
                response.append(temp_dict)

        # TODO: 如果是不是物理机
        if not response:
            s3 = subprocess.Popen("df | sed 1d | awk '{SUM +=$2} END {print SUM}'",
                                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            s3_output = s3.stdout.read()
            capacity = int(s3_output) / 1024 / 1024
            response.append({'capacity': capacity, 'iface_type': 'not a physics machine'})

        return response

    def mega_patter_match(self, needle):
        # grep_pattern = {'Slot': 'slot', 'Raw Size': 'capacity', 'Inquiry': 'model', 'PD Type': 'iface_type'}
        for key, value in self.grep_pattern.items():
            if needle.startswith(key):
                return value
        return False


class Main(DiskPlugin):
    def collect(self):
        # print('collect')
        filter_keys = ['Manufacturer', 'Serial Number', 'Product Name', 'UUID', 'Wake-up Type']
        raw_data = {}

        for key in filter_keys:
            res = subprocess.Popen("sudo dmidecode -t system|grep '%s'" % key,
                                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.stderr.read():
                exit("sudo dmidecode -t system|grep '%s'" % key)

            res_output = res.stdout.read()
            res_output = data_format_convert(res_output)

            res_validate = res_output.split(':')[1].strip()
            raw_data[key] = res_validate

        data = {
            "asset_type": 'server',
            'manufactory': raw_data['Manufacturer'],
            'sn': raw_data['Serial Number'],
            'model': raw_data['Product Name'],
            'uuid': raw_data['UUID'],
            'wake_up_type': raw_data['Wake-up Type']
        }

        data.update(self.nicinfo)
        data.update(self.cpuinfo)
        data.update(self.raminfo)
        data.update(self.osinfo)
        data.update(self.diskinfo())
        print(data)
        return data

    @property
    def nicinfo(self):
        # nics = []
        # nic_res = subprocess.Popen("ifconfig -a | awk '{print $1}' | grep -i e | egrep -vi 'inet|Interrupt'",
        #                            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # if nic_res.stderr.read():
        #     exit("ifconfig -a | awk '{print $1}' | grep -i e | egrep -vi 'inet|Interrupt' failed .. ")
        #
        # nic_res_output = nic_res.stdout.read()
        # nic_res_output = data_format_convert(nic_res_output)
        # for nic in nic_res_output.split('\n'):
        #     nics.append(nic)

        res = subprocess.Popen("ifconfig -a", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw_data = res.stdout.read()
        raw_data = data_format_convert(raw_data).split("\n")

        nic_dic = {}
        next_line = False
        last_mac_addr = None
        for line in raw_data:
            if next_line:
                next_line = False
                nic_name = last_mac_addr.split()[0]
                mac_addr = last_mac_addr.split("HWaddr")[1].strip()

                if 'inet' in line:
                    ip_addr = line.split("inet addr:")[1].split()[0]
                    network = line.split("Bcast:")[1].split()[0]
                    netmask = line.split("Mask:")[1].split()[0]
                else:
                    ip_addr = 'unknown'
                    network = 'unknown'
                    netmask = 'unknown'

                if mac_addr not in nic_dic:
                    nic_dic[mac_addr] = {
                        'name': nic_name,
                        'mac': mac_addr,
                        'mask': netmask,
                        'network': network,
                        'bonding': 0,
                        'model': 'unknown',
                        'ip': ip_addr,
                    }
                else:  # mac already exist , must be boding address
                    if '%s_bonding_addr' % mac_addr not in nic_dic:
                        random_mac_addr = '%s_bonding_addr' % mac_addr
                    else:
                        random_mac_addr = '%s_bonding_addr2' % mac_addr

                    nic_dic[random_mac_addr] = {
                        'name': nic_name,
                        'mac': random_mac_addr,
                        'mask': netmask,
                        'network': network,
                        'bonding': 1,
                        'model': 'unknown',
                        'ip': ip_addr,
                    }

            if "HWaddr" in line:
                next_line = True
                last_mac_addr = line

        nic_list = []
        for k, v in nic_dic.items():
            nic_list.append(v)

        return {'nic': nic_list}

    @property
    def cpuinfo(self):
        raw_data = {
            'cpu_model': "cat /proc/cpuinfo | grep 'model name' | head -1 | awk -F':' '{print $2}'",
            'physical_count': "cat /proc/cpuinfo | grep 'physical id' | sort | uniq | wc -l",
            'logic_count': "cat /proc/cpuinfo |grep  'processor'|wc -l ",
        }

        for k, cmd in raw_data.items():
            raw_data[k] = commands.getoutput(cmd).strip()

        return raw_data

    @property
    def raminfo(self):
        # print('raminfo')
        # raw_data = subprocess.check_output(["sudo", "dmidecode" ,"-t", "17"])
        raw_list = commands.getoutput("sudo dmidecode -t 17 | sed '1,3d'").split("\n")

        raw_info = {
            'ram': []
        }

        info_needed = {
            'DIMM': 'slot',  # 内存条位置
            'Size': 'capacity',  # 内存条容量
            'Manufacturer': 'manufactory',  # 生产商
            'Serial Number': 'sn',  # SN号
            'Asset Tag': 'asset_tag',  # 资产标识
            'DDR': 'type'  # 内存条类型
        }

        count = 0
        tmp_dict = {}
        for line in raw_list:
            count += 1
            if count < 21:  # raw_list 里，每21行是一个信息段，具体视命令执行结果而定
                for k, v in info_needed.items():
                    if k in line:
                        valid_info = line.split(':')[1].strip()
                        if valid_info != '':
                            tmp_dict[v] = valid_info
                        else:
                            tmp_dict['flag'] = 'invalid'  # 内存槽未插满时

            elif count == 21:
                if 'flag' in tmp_dict:  # 去除未插入内存条的槽
                    pass
                else:
                    raw_info['ram'].append(tmp_dict)
            else:
                tmp_dict = {}
                count = 1

        for i in raw_info['ram']:
            i['capacity'] = i['capacity'].split()[0]

        total_size_kb = commands.getoutput("cat /proc/meminfo|grep MemTotal ").split(":")[1].split()[0]

        total_size_mb = int(total_size_kb) / 1024
        if not raw_info['ram']:
            raw_info['ram'].append({'capacity': total_size_mb})

        total_size_gb = int(total_size_kb) / 1024 / 1024
        raw_info['ram_size'] = '%sGB' % total_size_gb

        # print(raw_info)
        return raw_info

    @property
    def osinfo(self):
        # print('osinfo')
        # distributor = subprocess.check_output(" lsb_release -a|grep 'Distributor ID'",shell=True).split(":")
        # release  = subprocess.check_output(" lsb_release -a|grep Description",shell=True).split(":")
        distributor = commands.getoutput(" lsb_release -a|grep 'Distributor ID'").split(":")
        release = commands.getoutput(" lsb_release -a|grep Description").split(":")
        data_dic = {
            "os_distribution": distributor[1].strip() if len(distributor) > 1 else 'unknown',
            "os_release": release[1].strip() if len(release) > 1 else 'unknown',
            "os_type": "linux",
        }
        # print(data_dic)
        return data_dic


if __name__ == "__main__":
    import logging

    try:
        obj = Main()
        obj.collect()
    except Exception as e:
        logging.exception(e)
