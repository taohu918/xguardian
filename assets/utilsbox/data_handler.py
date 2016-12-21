# -*- coding: utf-8 -*-
# __author__: taohu

import json
from assets import models
from django.utils import timezone
from assets.utilsbox.log import logger
from userauth.models import UserProfile
from django.core.exceptions import ObjectDoesNotExist


# import sys
#
# reload(sys)
# sys.setdefaultencoding("utf-8")


class DataValidityCheck(object):
    def __init__(self, request):
        self.request = request
        self.mandatory_check_list = ['sn', 'asset_uid', 'asset_type']
        self.no_err_msg_in_response = True  # 信息记录中是否有 err 的记录
        self.clean_data = None
        self.agent_asset_uid = None  # agent 采集的资产 uid

        self.field_sets = {
            'asset': ['manufactory'],
            'server': ['model', 'cpu_socket', 'cpu_cores', 'cpu_model', 'raid_type', 'os_distributor'],
            'networkdevice': []
        }
        self.response = {
            'error': [],
            'info': [],
            'warning': []
        }

        self.server_obj = None
        self.asset_uid = None
        self.successful = False
        self.update_successful = False
        self.data_validation = self.data_is_valid()

    def data_is_valid(self):
        """校验数据是否可用"""
        try:
            data = self.request.data.get("asset_data")  # unicode
            data = json.loads(data)
            if self.mandatory_check(data):
                self.clean_data = data
                self.asset_uid = str(data['asset_uid'])  # agent 上报的资产uid, 新资产 uid=0
                return True
            else:
                return False

        except Exception as e:
            self.response_msg('error', 'data_is_valid', str(e))
            self.no_err_msg_in_response = False
            return False

    def mandatory_check(self, data):
        for key in self.mandatory_check_list:
            if key not in data:
                self.response_msg('error', 'mandatory_check', "Can't find key<%s> in reporting data" % key)
                self.no_err_msg_in_response = False
        return self.no_err_msg_in_response

    def response_msg(self, msg_type, key, msg):
        """
        :param msg_type -> 'error' 'info' 'warning'
        :param key -> error overview
        :param msg -> error content
        """
        if msg_type in self.response:
            self.response[msg_type].append({key: msg})
        else:
            raise ValueError

    def asset_type_existing(self):
        """
        :func  ensure data from agent contains asset_type
        """
        if not hasattr(self.server_obj, self.clean_data['asset_type']):
            return True
        else:
            return False

    def field_verify(self, data_set, field_key, data_type, required=True, mth=None):
        field_val = data_set.get(field_key)  # "model": "Latitude 3330"
        if field_val != 0:
            try:
                data_set[field_key] = data_type(field_val)
            except ValueError as e:
                self.response_msg(
                    'error',
                    mth,
                    # "Data type of field<%s> isn't [%s], plz check " % (field_key, data_type))
                    str(e))
                return False

        elif required:  # 如果为必须需要字段
            self.response_msg(
                'error',
                mth,
                "No value provided for field<%s> in reporting data [%s]" % (field_key, data_set))
            return False

    def generate_asset_uid(self):
        import hashlib
        if 'uuid' not in self.clean_data:
            self.clean_data['uuid'] = None
        unique_str = "%s%s%s" % (self.clean_data['asset_type'], self.clean_data['sn'], self.clean_data['uuid'])

        obj = hashlib.md5()
        obj.update(unique_str.encode('utf-8'))

        tmp_str = obj.hexdigest()[-4:].upper()
        self.asset_uid = self.clean_data['sn'] + '-00' + '%s' % ord(tmp_str[0]) + tmp_str[1:]
        self.asset_uid = obj.hexdigest().upper()
        return self.asset_uid


class Handler(DataValidityCheck):
    def data_incorporated(self):
        try:
            if self.data_validation:  # if data_is_valid return True, then this func will be called.
                if self.asset_uid == '0':
                    self.create_method(self.clean_data['asset_type'])
                else:
                    self.update_method(self.clean_data['asset_type'])
            self.successful = True
        except Exception as e:
            logger.details(e)

    def create_method(self, types):
        func = getattr(self, '_create_asset_%s' % types)
        func()

    def update_method(self, types):
        func = getattr(self, '_update_asset_%s' % types)
        func()

    def _create_asset_server(self):
        # 给新资产生成 uid
        self.generate_asset_uid()
        if self.asset_uid is None:
            self.response_msg('error', '_create_asset_server', 'generate_asset_uid() failed.')
            return False

        self.__add_server_obj()
        self.__add_manufactory()
        self.__add_cpu_component()
        self.__add_disk_component()
        self.__add_nic_component()
        self.__add_ram_component()
        self.__add_os_component()

        # log_msg = "Asset [<a href='/admin/assets/asset/%s/' target='_blank'>%s</a>] has been created!" % (
        #     self.server_obj.uid, self.server_obj)
        # self.response_msg('info', 'NewAssetOnline', log_msg)

    def __add_server_obj(self, ignore_errs=False, only_check_sn=False):
        self.field_verify(self.clean_data, 'model', str, mth='__add_server_obj')
        if self.no_err_msg_in_response or ignore_errs:  # no errors or ignore errors
            data_dic = {
                'uid': self.asset_uid,
                'sn': self.clean_data['sn'],
                'model': self.clean_data.get('model'),
                'hosted': self.clean_data.get('hosted'),
                'ram_size': self.clean_data.get('ram_size')
            }
            obj = models.Server(**data_dic)
            obj.save()

            log_msg = "Asset<%s> add new [server] record ." % self.asset_uid
            self.response_msg('info', '__add_server_obj', u'%s' % log_msg)
            log_handler(obj, '__add_server_obj', self.request.user, log_msg, event_type=1, component='server')

            self.add_successful = True

        if only_check_sn:
            self.server_obj = models.Server.objects.get(uid=self.asset_uid)
        else:
            self.server_obj = models.Server.objects.get(uid=self.asset_uid, sn=self.clean_data['sn'])

    def __add_manufactory(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'manufactory', str, mth='__check_manufactory')
            manufactory = self.clean_data.get('manufactory')
            if self.no_err_msg_in_response or ignore_errs:
                # 从现有数据库中检查生产厂商是否存在
                obj = models.Manufactory.objects.filter(manufactory=manufactory)
                if obj:
                    this_obj = obj[0]
                else:
                    this_obj = models.Manufactory(manufactory=manufactory)
                    this_obj.save()

                # 更新 server 表的对应字段（不能直接更新，需要使用表 Manufactory 的对象）
                self.server_obj.manufactory = this_obj
                self.server_obj.save()
                self.add_successful = True

        except Exception as e:
            self.response_msg('error', '__check_manufactory', str(e))
            self.add_successful = False

    def __add_cpu_component(self, ignore_errs=False):
        # try:
        self.field_verify(self.clean_data, 'cpu_model', str, mth='__add_cpu_component')
        self.field_verify(self.clean_data, 'cpu_socket', int, mth='__add_cpu_component')
        self.field_verify(self.clean_data, 'cpu_cores', int, mth='__add_cpu_component')
        self.field_verify(self.clean_data, 'cpu_processors', int, mth='__add_cpu_component')

        if self.no_err_msg_in_response or ignore_errs:
            data_set = {
                'asset_uid': self.server_obj,
                'cpu_model': self.clean_data.get('cpu_model'),
                'cpu_socket': self.clean_data.get('cpu_socket'),
                'cpu_cores': self.clean_data.get('cpu_cores'),
                'cpu_processors': self.clean_data.get('cpu_processors'),
            }

            obj = models.CPU(**data_set)
            obj.save()

            log_msg = "Asset<%s> add new [cpu] record with data [%s]" % (self.asset_uid, data_set)
            self.response_msg('info', '__add_cpu_component', log_msg)
            log_handler(self.server_obj, '__add_cpu_component', self.request.user, log_msg, event_type=1,
                        component='CPU')

            self.add_successful = True

            # except Exception as e:
            #     self.response_msg('error', '__add_cpu_component', str(e))
            #     log_handler(self.server_obj, '__add_cpu_component', self.request.user, str(e), event_type=4,
            #                 component='CPU')
            #     self.add_successful = False

    def __add_disk_component(self):
        disk_info = self.clean_data.get('disk')
        if self.clean_data['host_type'] == 'physical':
            for disk_item in disk_info:
                # disk_item: {u'slotx': {u'slot': u'slotx', u'model': u'Dell', u'iface': u'SAS', u'capacity': 48208}}
                for i in disk_item.values():
                    # disk_item.values(): [{u'slot': u'slotx', u'model': u'Dell', u'iface': u'SAS', u'capacity': 48208}]
                    # py3 doesn't support method: k, obj_value = disk_item.items()[0]
                    obj_value = i

                self.field_verify(obj_value, 'slot', str, mth='__add_disk_component')
                self.field_verify(obj_value, 'capacity', str, mth='__add_disk_component')
                self.field_verify(obj_value, 'iface', str, mth='__add_disk_component')
                self.field_verify(obj_value, 'model', str, mth='__add_disk_component')

                if self.no_err_msg_in_response:  # no processing when there's no error happend
                    data_set = {
                        'asset_uid': self.server_obj,
                        # 'sn': obj_value.get('sn'),    # 取消了硬盘sn号的采集
                        'capacity': obj_value.get('capacity'),
                        'iface': obj_value.get('iface'),
                        'manufactory': obj_value.get('manufactory'),
                        'model': obj_value.get('model'),
                        'slot': obj_value.get('slot'),
                    }

                    obj = models.Disk(**data_set)
                    obj.save()

                    log_msg = "Asset<%s> add new [disk] record with data [%s]" % (self.asset_uid, data_set)
                    self.response_msg('info', '__add_disk_component', log_msg)
                    log_handler(self.server_obj, '__add_disk_component', self.request.user, log_msg,
                                event_type=1,
                                component='Disk')

                    self.add_successful = True

        else:  # 非物理机, disk 信息为逻辑生成的, list 中只有一个元素(字典形式): disk_info[0]
            if self.no_err_msg_in_response:
                v = disk_info[0].values()[0]
                data_set = {
                    'asset_uid': self.server_obj,
                    'capacity': v.get('capacity'),
                    'iface': v.get('iface'),
                    'manufactory': v.get('manufactory'),
                    'model': v.get('model'),
                    'slot': v.get('slot'),
                }

                obj = models.Disk(**data_set)
                obj.save()

                log_msg = "Asset<%s> add new [disk] record with data [%s]" % (self.asset_uid, data_set)
                self.response_msg('info', '__add_disk_component', log_msg)
                log_handler(self.server_obj, '__add_disk_component', self.request.user, log_msg,
                            event_type=1,
                            component='Disk')

                self.add_successful = True

    def __add_nic_component(self):
        nic_info = self.clean_data.get('nic')
        assert nic_info, "nic_info is invalid"
        if self.clean_data['host_type'] == 'physical':
            for nic_item in nic_info:
                for i in nic_item.values():
                    obj_value = i
                self.field_verify(obj_value, 'mac', str)
                if self.no_err_msg_in_response:
                    data_set = {
                        'asset_uid': self.server_obj,
                        'bonding': obj_value.get('bonding'),
                        'ip': obj_value.get('ip'),
                        'mac': obj_value.get('mac'),
                        'mask': obj_value.get('mask'),
                        'model': obj_value.get('model'),
                        'name': obj_value.get('name'),
                        # 'network': obj_value.get('network'),
                    }

                    obj = models.NIC(**data_set)
                    obj.save()

                    log_msg = "Asset<%s> add new [nic] record with data [%s]" % (self.asset_uid, data_set)
                    self.response_msg('info', '__add_nic_component', log_msg)
                    log_handler(self.server_obj, '__add_nic_component', self.request.user, log_msg, event_type=1,
                                component='NIC')

                    self.add_successful = True

        else:  # 非物理机, disk 信息为逻辑生成的, list 中只有一个元素(字典形式): disk_info[0]
            if self.no_err_msg_in_response:
                v = nic_info[0].values()[0]
                data_set = {
                    'asset_uid': self.server_obj,
                    'bonding': v.get('bonding'),
                    'ip': v.get('ip'),
                    'mac': v.get('mac'),
                    'mask': v.get('mask'),
                    'model': v.get('model'),
                    'name': v.get('name'),
                }

                obj = models.NIC(**data_set)
                obj.save()

                log_msg = "Asset<%s> add new [nic] record with data [%s]" % (self.asset_uid, data_set)
                self.response_msg('info', '__add_nic_component', log_msg)
                log_handler(self.server_obj, '__add_nic_component', self.request.user, log_msg, event_type=1,
                            component='NIC')

                self.add_successful = True

    def __add_ram_component(self):
        ram_info = self.clean_data.get('ram')
        assert ram_info, 'ram_info is invalid'
        if self.clean_data['host_type'] == 'physical':
            for ram_item in ram_info:
                for i in ram_item.values():
                    obj_value = i
                self.field_verify(obj_value, 'capacity', str)
                if self.no_err_msg_in_response:
                    data_set = {
                        'asset_uid': self.server_obj,
                        'capacity': obj_value.get('capacity'),
                        'manufactory': obj_value.get('manufactory'),
                        'model': obj_value.get('model'),
                        'slot': obj_value.get("slot"),
                        'sn': obj_value.get('sn'),
                        'type': obj_value.get('type'),
                    }
                    obj = models.RAM(**data_set)
                    obj.save()

                    log_msg = "Asset<%s> add new [ram] record with data [%s]" % (self.asset_uid, data_set)
                    self.response_msg('info', '__add_ram_component', log_msg)
                    log_handler(self.server_obj, '__add_ram_component', self.request.user, log_msg,
                                event_type=1,
                                component='RAM')

                    self.add_successful = True

        else:
            if self.no_err_msg_in_response:
                v = ram_info[0].values()[0]
                data_set = {
                    'asset_uid': self.server_obj,
                    'capacity': v.get('capacity'),
                    'manufactory': v.get('manufactory'),
                    'model': v.get('model'),
                    'slot': v.get("slot"),
                    'sn': v.get('sn'),
                    'type': v.get('type'),
                }
                obj = models.RAM(**data_set)
                obj.save()

                log_msg = "Asset<%s> add new [ram] record with data [%s]" % (self.asset_uid, data_set)
                self.response_msg('info', '__add_ram_component', log_msg)
                log_handler(self.server_obj, '__add_ram_component', self.request.user, log_msg,
                            event_type=1,
                            component='RAM')

                self.add_successful = True

    def __add_os_component(self, ignore_errs=False):
        self.field_verify(self.clean_data, 'os_classification', str)
        self.field_verify(self.clean_data, 'os_codename', str)
        self.field_verify(self.clean_data, 'os_description', str)
        self.field_verify(self.clean_data, 'os_distributor', str)
        self.field_verify(self.clean_data, 'os_release', str)

        if self.no_err_msg_in_response or ignore_errs:
            data_set = {
                'asset_uid': self.server_obj,
                'os_classification': self.clean_data.get('os_classification'),
                'os_codename': self.clean_data.get('os_codename'),
                'os_description': self.clean_data.get('os_description'),
                'os_distributor': self.clean_data.get('os_distributor'),
                'os_release': self.clean_data.get('os_release'),
            }
            obj = models.OS(**data_set)
            obj.save()

            log_msg = "Asset<%s> add new [os] record with data [%s]" % (self.asset_uid, data_set)
            self.response_msg('info', '__add_os_component', log_msg)
            log_handler(self.server_obj, '__add_os_component', self.request.user, log_msg, event_type=1,
                        component='OS')

            self.add_successful = True

    def _update_asset_server(self):
        """ update server record according to data from agent """
        self.__update_server_component()

        self.__update_disk_record()
        self.__update_nic_record()
        self.__update_ram_record()
        self.__update_cpu_record()

        # manufactory = self.__update_manufactory_component()
        self.update_successful = True

    def __update_server_component(self):
        update_fields = ['model', ]
        self.server_obj = models.Server.objects.get(uid=self.asset_uid)
        self.__compare_componet(model_obj=self.server_obj, update_fields=update_fields, data_source=self.clean_data)

    def __compare_componet(self, model_obj, update_fields, data_source):
        """
        :param model_obj: 需要进行对比的 对象
        :param update_fields: 需要进行比对的字段
        :param data_source:
        :return:
        """
        for field in update_fields:  # base on data in mysql
            val_from_db = getattr(model_obj, field)
            val_from_agent = data_source.get(field)
            if val_from_agent:
                if str(val_from_db) != str(val_from_agent):
                    # a special method, update data in model.
                    # Retrieving a single field instance of a model by str
                    db_field_obj = model_obj._meta.get_field(field)  #
                    db_field_obj.save_form_data(model_obj, val_from_agent)
                    model_obj.update_date = timezone.now()
                    model_obj.save()

                    log_msg = u"Table<%s> Field<%s> Changed: From '%s' to '%s' " % (
                        'Server', field, val_from_db, val_from_agent)
                    self.response_msg('info', '__compare_componet', log_msg)
                    log_handler(self.server_obj, 'FieldChanged', self.request.user, log_msg)
                    self.update_successful = True
            else:
                self.response_msg('warning', '__compare_componet',
                                  "Asset component [%s]'s field [%s] is not provided in reporting data " % (
                                      model_obj, field))

    @staticmethod
    def dict_to_str(list_dict):
        """
        :func: 对传入的 [{KEY1: {key: value}}, {KEY2: {key: value}}] 类型数据中的 嵌套字典进行排序
        :param list_dict: [{KEY1: {key: value}}, {KEY2: {key: value}}]
        :return:
        """
        new_list_dict = []
        for index, item in enumerate(list_dict):  # item: {KEY: {key: value}}
            # 对 {key: value} 进行排序
            for element in item.items():  # 这里item.items() 产生只有一个元素的可迭代对象(in py3) 或者列表(in py2)
                key, value = element
                item[key] = json.dumps(value, sort_keys=True)

            # 对 {KEY: {}} 进行排序
            json_dict = json.dumps(item, sort_keys=True)

            new_list_dict.append(json_dict)
        return new_list_dict

    @staticmethod
    def str_to_dict(list_str):
        new_list = []
        for index, item in enumerate(list_str):
            # 去 json, item: '{KEY: "{key: value}"}' => anti_json_item: {KEY: "{key: value}"}
            anti_json_item = json.loads(item)

            # 去 json, element: {KEY: "{key: value}"} => anti_json_item: {KEY: {key: value}}
            for element in anti_json_item.items():
                key, value = element
                anti_json_item[key] = json.loads(value)

            new_list.append(anti_json_item)
        return new_list

    @staticmethod
    def convert_db_data_format_to_agent_data_format(objs, fields, first_key):
        """
        :tip: 转变 db 中的记录格式，使其和 agent 汇报的数据格式一致 [ KEY: { key: value } ]
        :param objs: 从 db 中匹配到的 model 对象
        :param fields: 需要比对的字段列表
        :param first_key: 指定作为 KEY 的字段
        :return: 返回 agnet_data 形式的数据列表 [ KEY: { key: value } ]
        """
        tmp_list = []
        for obj in objs:  # obj 每行数据
            tmp_dict = {}
            for item in fields:
                val = getattr(obj, item)
                if not val:
                    val = ""
                # elif hasattr(val, 'isdigit'):
                #     if val.isdigit():
                #         val = int(val)
                tmp_dict.update({item: val})

            tmp_list.append({getattr(obj, first_key): tmp_dict})

        return tmp_list

    def __update_disk_record(self):
        """
        :fields: 改列表要包括 db 中对应表的所有有效字典
        :return:
        """
        disk_list_agent = self.clean_data['disk']
        # disk_list_agent = [
        #     {"0": {"capacity": "2860515 MB", "iface": "SAS", "manufactory": "Dell",
        #            "model": "TOSHIBA MG03SCA300      DG0263H0A0VOFVL9", "slot": "0"}},
        #     {"1": {"capacity": "2860515 MB", "iface": "SAS", "manufactory": "IBM",
        #            "model": "TOSHIBA MG03SCA300      DG0263I0A0R7FVL9", "slot": "1"}}]

        fields = ['capacity', 'iface', 'manufactory', 'model', 'slot', ]
        objs = self.server_obj.disk_set.all()
        disk_list_db = self.convert_db_data_format_to_agent_data_format(objs, fields, 'slot')

        set_disk_list_agent = set(self.dict_to_str(disk_list_agent))
        set_disk_list_db = set(self.dict_to_str(disk_list_db))

        set_records_need_to_be_add = set_disk_list_agent - set_disk_list_db
        set_records_need_to_be_del = set_disk_list_db - set_disk_list_agent

        records_need_to_be_add = self.str_to_dict(set_records_need_to_be_add)
        records_need_to_be_del = self.str_to_dict(set_records_need_to_be_del)

        for item in records_need_to_be_del:
            for k, v in item.items():
                models.Disk.objects.filter(asset_uid=self.asset_uid, slot=k).delete()

        if records_need_to_be_add:
            self.clean_data['disk'] = records_need_to_be_add
            self.__add_disk_component()

        return

    def __update_nic_record(self):
        nic_list_agent = self.clean_data['nic']
        # nic_list_agent = [
        #     {'15': {'model': '[00000015] Intel(R) Dual Band Wireless-AC 3160', 'ip': '10.1.0.96',
        #             'mac': '15:DE:1A:72:22:BB', 'name': '15', 'mask': '255.255.255.0', 'bonding': 'no'}},
        #     {'17': {'model': '[00000017] Realtek PCIe GBE Family Controller', 'ip': '',
        #             'mac': 'E0:DB:55:FB:0F:5E', 'name': '17', 'mask': '', 'bonding': 'no'}}]

        fields = ['bonding', 'ip', 'mac', 'mask', 'model', 'name', ]
        objs = self.server_obj.nic_set.all()
        nic_list_db = self.convert_db_data_format_to_agent_data_format(objs, fields, 'name')

        set_nic_list_agent = set(self.dict_to_str(nic_list_agent))
        set_nic_list_db = set(self.dict_to_str(nic_list_db))

        set_records_need_to_be_add = set_nic_list_agent - set_nic_list_db
        set_records_need_to_be_del = set_nic_list_db - set_nic_list_agent

        records_need_to_be_add = self.str_to_dict(set_records_need_to_be_add)
        records_need_to_be_del = self.str_to_dict(set_records_need_to_be_del)

        for item in records_need_to_be_del:
            for k, v in item.items():
                # print(k, v)
                models.NIC.objects.get(asset_uid=self.asset_uid, name=k).delete()

        if records_need_to_be_add:
            self.clean_data['nic'] = records_need_to_be_add
            self.__add_nic_component()

        return

    def __update_ram_record(self):
        ram_list_agent = self.clean_data['ram']
        # ram_list_agent = [
        #     {"DIMM_A1": {"capacity": "16384 MB", "manufactory": "00CE04B300CE", 'model': 'Physical Memory',
        #                  "slot": "DIMM_A1", "sn": "13E44142", "type": "DDR3"}},
        #     {"DIMM_A2": {"capacity": "16384 MB", "manufactory": "00CE04B300CE", 'model': 'Physical Memory',
        #                  "slot": "DIMM_A2", "sn": "13E440A7", "type": "DDR3"}}]

        fields = ['capacity', 'manufactory', 'model', 'slot', 'sn', 'type', ]
        objs = self.server_obj.ram_set.all()
        ram_list_db = self.convert_db_data_format_to_agent_data_format(objs, fields, 'slot')

        set_ram_list_agent = set(self.dict_to_str(ram_list_agent))
        set_ram_list_db = set(self.dict_to_str(ram_list_db))

        set_records_need_to_be_add = set_ram_list_agent - set_ram_list_db
        set_records_need_to_be_del = set_ram_list_db - set_ram_list_agent

        records_need_to_be_add = self.str_to_dict(set_records_need_to_be_add)
        records_need_to_be_del = self.str_to_dict(set_records_need_to_be_del)

        for item in records_need_to_be_del:
            for k, v in item.items():
                # print(k, v)
                models.RAM.objects.filter(asset_uid=self.asset_uid, slot=k).delete()

        if records_need_to_be_add:
            self.clean_data['ram'] = records_need_to_be_add
            self.__add_ram_component()

        return

    def __update_cpu_record(self):
        fields = ['cpu_model', 'cpu_socket', 'cpu_cores', 'cpu_processors']
        # self.clean_data['cpu_model'] = 'China Kylin'
        cpu_obj = models.CPU.objects.get(asset_uid=self.asset_uid)
        for item in fields:
            if getattr(cpu_obj, item) != self.clean_data[item]:
                setattr(cpu_obj, item, self.clean_data[item])
        cpu_obj.save()


def log_handler(server_obj, event_name, user, detail, event_type=1, component=None, memo=None):
    if not user.id:
        # user = UserProfile.objects.filter(is_admin=True).last()
        # user_id = user.id
        user_id = None
    else:
        user_id = user.id

    if not memo:
        memo = 'no memo.'

    if not server_obj:
        server_obj = None

    try:
        log_obj = models.EventLog(
            asset_uid=server_obj,
            event_name=event_name,
            event_type=event_type,
            user_id=user_id,
            # detail=detail,
            detail='',
            component=component,
            memo=memo)

        log_obj.save()
        return True
    except Exception as e:
        print('log_handler', e)
        return False
