# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")

# http://pilotfiber.dl.sourceforge.net/project/pywin32/pywin32/Build%20220/pywin32-220.win-amd64-py2.7.exe
# pip install wmi

import platform
import win32com
import wmi


class Main(object):
    def __init__(self):
        self.wmi_obj = wmi.WMI()
        self.wmi_service_obj = win32com.client.Dispatch("WbemScripting.SWbemLocator")
        self.wmi_service_connector = self.wmi_service_obj.ConnectServer(".", "root\cimv2")
        self.data = {
            'os_distributor': platform.system(),
            'os_description': "%s %s %s" % (platform.system(), platform.release(), platform.architecture()[0]),
            'os_release': platform.release(),
            'os_codename': platform.version(),
            'os_classification': platform.system().lower(),
            'asset_type': 'server',
            'host_type': 'physical',
        }

    def collect(self):
        self.data.update(self.cpu_info)
        self.data.update(self.get_ram_info())
        self.data.update(self.get_server_info())
        self.data.update(self.get_disk_info())
        self.data.update(self.get_nic_info())
        return self.data

    @property
    def cpu_info(self):
        data = {}
        cpu_lists = self.wmi_obj.Win32_Processor()
        # for cpu in cpu_lists:
        #     print(cpu)

        data["cpu_model"] = cpu_lists[0].Name
        data["cpu_socket"] = len(cpu_lists)

        cpu_cores_count = 0
        cpu_logical_processors_count = 0
        for cpu in cpu_lists:
            cpu_cores_count += cpu.NumberOfCores
            cpu_logical_processors_count += cpu.NumberOfLogicalProcessors

        data["cpu_cores"] = cpu_cores_count
        data["cpu_processors"] = cpu_logical_processors_count

        return data

    def get_ram_info(self):
        data = []
        ram_size = 0
        ram_info = self.wmi_service_connector.ExecQuery("Select * from Win32_PhysicalMemory")
        mb = 1024 * 1024
        for item in ram_info:  # item -> <COMObject <unknown>>
            # print(item)
            capacity = int(item.Capacity) / mb
            item_data = {
                "capacity": str(int(capacity)) + ' MB',  # 多一级int是为了取整
                "manufactory": item.Manufacturer,
                "model": item.Caption,
                "slot": item.DeviceLocator.strip(),
                "sn": item.SerialNumber,
                "type": "",
            }
            # data.append(item_data)
            data.append({item.DeviceLocator.strip(): item_data})

            ram_size += int(capacity) / 1024
            self.data.update({'ram_size': '%s GB' % ram_size}, )

        return {"ram": data}

    def get_server_info(self):
        computer_info = self.wmi_obj.Win32_ComputerSystem()[0]
        system_info = self.wmi_obj.Win32_OperatingSystem()[0]
        data = {
            'manufactory': computer_info.Manufacturer,
            'model': computer_info.Model,
            'wake_up_type': computer_info.WakeUpType,
            'sn': system_info.SerialNumber,
        }
        # print(computer_info)
        return data

    def get_disk_info(self):
        data = []
        iface_choices = ["SAS", "SCSI", "SATA", "SSD", "IDE"]
        unit_mb = 1024 * 1024
        unit_gb = 1024 * 1024 * 1024

        for disk in self.wmi_obj.Win32_DiskDrive():
            # print(disk)
            item_data = {}
            for iface in iface_choices:
                if iface in disk.InterfaceType:
                    item_data['iface'] = iface
                    break
            else:
                item_data['iface'] = 'unknown(out of range)'
            item_data['slot'] = 'slot' + str(disk.Index)
            # item_data['sn'] = disk.SerialNumber
            item_data['model'] = disk.Model
            item_data['manufactory'] = disk.Manufacturer
            item_data['capacity'] = str(int(int(disk.Size) / unit_mb)) + ' MB'  # 多一级int是为了取整
            data.append(item_data)

        new_data = []
        for item in data:
            new_data.append({item['slot']: item})

        return {'disk': new_data}

    def get_nic_info(self):
        data = []
        useless_nic_list = ['vpn', 'virtual', 'bluetooth']

        for nic in self.wmi_obj.Win32_NetworkAdapterConfiguration():
            # print(nic)
            item_data = {}

            # 判断是否为需要的网卡信息
            flag = False
            for useless_item in useless_nic_list:
                if useless_item in nic.Caption.lower():
                    flag = True

            if flag:
                continue

            item_data['bonding'] = ''

            if nic.MACAddress is not None:
                # print(nic)
                item_data['mac'] = nic.MACAddress
                item_data['model'] = nic.Caption
                item_data['name'] = str(nic.Index)

                if nic.IPAddress is not None:
                    item_data['ip'] = nic.IPAddress[0]
                    item_data['mask'] = nic.IPSubnet[0]
                else:
                    item_data['ip'] = ''
                    item_data['mask'] = ''

            else:
                continue

            data.append({nic.Index: item_data})

        return {'nic': data}


if __name__ == "__main__":
    import logging
    import json

    try:
        obj = Main()
        res = obj.collect()
        print(json.dumps(res, sort_keys=True, indent=4))
        # print(obj.get_nic_info())
    except Exception as e:
        logging.exception(e)
