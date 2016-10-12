# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

import os
import commands
import re
import sys


class DiskPlugin(object):
    def echo(self, msg, line=getattr(sys, '_getframe')().f_lineno):
        """
        :func: self.echo(msg, getattr(sys, '_getframe')().f_lineno)
        :param msg: message to print
        :param line: getattr(sys, '_getframe')().f_lineno
        :return:
        """
        import inspect
        import os
        print("\033[1;33m %s.%s.%s \033[0m" % (os.path.abspath(__file__), self.__class__.__name__, inspect.stack()[1][3]))
        print("\033[1;33m line %s: output -> %s \033[0m" % (line, str(msg)))

    def centos(self):
        result = {'physical_disk_driver': []}

        try:
            script_path = os.path.dirname(os.path.abspath(__file__))
            prepare_step = commands.getstatusoutput("chmod +x %s/MegaCli" % script_path)

            shell_command = "sudo %s/MegaCli  -PDList -aALL" % script_path
            output = commands.getstatusoutput(shell_command)
            result['physical_disk_driver'] = self.parse(output[1])

        except Exception, e:
            result['error'] = e
        return result

    def parse(self, content):
        """
        解析shell命令返回结果
        :param content: shell 命令结果
        :return:解析后的结果
        """
        response = []
        result = []
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
        return response

    def mega_patter_match(self, needle):
        grep_pattern = {'Slot': 'slot', 'Raw Size': 'capacity', 'Inquiry': 'model', 'PD Type': 'iface_type'}
        for key, value in grep_pattern.items():
            if needle.startswith(key):
                return value
        return False


class Main(DiskPlugin):
    def collect(self):
        # print('collect')
        filter_keys = ['Manufacturer', 'Serial Number', 'Product Name', 'UUID', 'Wake-up Type']
        raw_data = {}

        for key in filter_keys:
            try:
                res = commands.getoutput("sudo dmidecode -t system|grep '%s'" % key).strip()
                res_validate = res.split(':')[1].strip()
                raw_data[key] = res_validate

            except Exception, e:
                print e
                raw_data[key] = 'ErrorMsg'

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
        data.update(self.centos())
        return data

    @property
    def nicinfo(self):
        # print('nicinfo')
        # tmp_f = file('/tmp/bonding_nic').read()
        # raw_data= subprocess.check_output("ifconfig -a",shell=True)
        raw_data = commands.getoutput("ifconfig -a").split("\n")

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
        # print('cpuinfo')
        raw_data = {
            'cpu_model': "cat /proc/cpuinfo | grep 'model name' | head -1 | awk -F':' '{print $2}'",
            'physical_count': "cat /proc/cpuinfo | grep 'physical id' | sort | uniq | wc -l",
            'logic_count': "cat /proc/cpuinfo |grep  'processor'|wc -l ",
        }

        for k, cmd in raw_data.items():
            try:
                # cmd_res = subprocess.check_output(cmd,shell=True)
                raw_data[k] = commands.getoutput(cmd).strip()
            except ValueError, e:
                print e

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
            if count < 21:
                for k, v in info_needed.items():
                    if k in line:
                        # print(line)
                        valid_info = line.split(':')[1].strip()
                        if valid_info != '':
                            tmp_dict[v] = valid_info
                        else:
                            tmp_dict['flag'] = 'invalid'

            elif count == 21:
                if 'flag' in tmp_dict:  # 去除未插入内存条的槽
                    pass
                else:
                    raw_info['ram'].append(tmp_dict)
            else:
                tmp_dict = {}
                count = 1

        # total_size_mb = 0
        # for item in raw_info['ram']:
        #     total_size_mb += int(item['capacity'].split('MB')[0].split('mb')[0])
        #

        total_size_kb = commands.getoutput("cat /proc/meminfo|grep MemTotal ").split(":")[1].split()[0]
        total_size_mb = int(total_size_kb) / 1024

        raw_info['ram_size'] = total_size_mb

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
    obj = Main()
    print obj.collect()
