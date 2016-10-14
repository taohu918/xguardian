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
            'os_type': platform.system(),
            'os_release': "%s %s  %s " % (platform.release(), platform.architecture()[0], platform.version()),
            'os_distribution': "%s %s" % (platform.system(), platform.version()),
            'asset_type': 'server'
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
        cpu_core_count = 0
        data["physical_count"] = len(cpu_lists)

        for cpu in cpu_lists:
            cpu_core_count += cpu.NumberOfCores

        data["cpu_model"] = cpu_lists[0].Name
        data["logic_count"] = cpu_core_count
        return data

    def get_ram_info(self):
        data = []
        ram_info = self.wmi_service_connector.ExecQuery("Select * from Win32_PhysicalMemory")
        mb = int(1024 * 1024)
        for item in ram_info:  # item -> <COMObject <unknown>>
            ram_size = int(item.Capacity) / mb
            item_data = {
                "slot": item.DeviceLocator.strip(),
                "capacity": ram_size,
                "model": item.Caption,
                "manufactory": item.Manufacturer,
                "sn": item.SerialNumber,
            }
            data.append(item_data)
        # for i in data:
        #    print i
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
        # print data
        return data

    def get_disk_info(self):
        data = []
        iface_choices = ["SAS", "SCSI", "SATA", "SSD"]
        unit_gb = 1024 * 1024 * 1024

        for disk in self.wmi_obj.Win32_DiskDrive():
            item_data = {}
            for iface in iface_choices:
                if iface in disk.Model:
                    item_data['iface_type'] = iface
                    break
            else:
                item_data['iface_type'] = 'unknown(out of range)'
            item_data['slot'] = 'slot'+str(disk.Index)
            item_data['sn'] = disk.SerialNumber
            item_data['model'] = disk.Model
            item_data['manufactory'] = disk.Manufacturer
            item_data['capacity'] = int(disk.Size) / unit_gb
            data.append(item_data)
        return {'physical_disk_driver': data}

    def get_nic_info(self):
        data = []
        for nic in self.wmi_obj.Win32_NetworkAdapterConfiguration():
            item_data = {}
            if nic.MACAddress is not None:
                item_data['mac'] = nic.MACAddress
                item_data['model'] = nic.Caption
                item_data['name'] = nic.Index

                if nic.IPAddress is not None:
                    item_data['ip'] = nic.IPAddress[0]
                    item_data['mask'] = nic.IPSubnet
                else:
                    item_data['ip'] = ''
                    item_data['mask'] = ''

                # bonding = 0
                data.append(item_data)
        return {'nic': data}


if __name__ == "__main__":
    collect_conduct = Main()
    print collect_conduct.collect()
