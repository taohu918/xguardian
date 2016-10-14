# -*- coding: utf-8 -*-
# __author__: taohu

import json
from assets import models
from django.utils import timezone
from userauth.models import UserProfile
from django.core.exceptions import ObjectDoesNotExist
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class DataValidityCheck(object):
    def __init__(self, request):
        self.request = request
        self.mandatory_keys = ['sn', 'asset_uid', 'asset_type', 'kinds']
        self.field_sets = {
            'asset': ['manufactory'],
            'server': [
                'model', 'cpu_count', 'cpu_core_count', 'cpu_model', 'raid_type', 'os_type', 'os_distribution',
                'os_release'],
            'networkdevice': []
        }
        self.response = {
            'error': [],
            'info': [],
            'warning': []
        }

        self.clean_data = None
        self.agent_asset_uid = None  # agent 采集的资产 uid
        self.server_obj = None
        self.asset_uid = None
        self.add_successful = False
        self.update_successful = False
        self.kinds = None  # 资产类型：物理机、虚拟机
        self.data_validation = self.data_is_valid()

    def data_is_valid(self):
        """校验数据是否可用"""
        # self.request.data --> QueryDict
        data = self.request.data.get("asset_data")  # unicode
        if data:
            try:
                data = json.loads(data)
                self.mandatory_check(data)
                self.clean_data = data
                self.agent_asset_uid = str(data['asset_uid'])
                self.kinds = str(data['kinds'])
                if not self.response['error']:
                    return True
            except ValueError, e:
                self.response_msg('error', 'data_is_valid', str(e))
                return False
        else:
            self.response_msg('error', 'data_is_valid', "The reported asset data is not valid or provided")
        return False

    def mandatory_check(self, data):
        for key in self.mandatory_keys:
            if key not in data:
                self.response_msg(
                    'error',
                    'mandatory_check',
                    "Can't find key<%s> in reporting data" % key)
        else:
            if self.response['error']:
                return False

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
            except ValueError, e:
                self.response_msg(
                    'error',
                    mth,
                    "Data type of field<%s> isn't [%s], plz check " % (field_key, data_type))
                return False

        elif required:  # 如果为必须需要字段
            self.response_msg(
                'error',
                mth,
                "No value provided for field<%s> in reporting data [%s]" % (field_key, data_set))
            return False

    def generate_asset_uid(self):
        import hashlib
        unique_str = "%s%s%s" % (self.clean_data['sn'], self.clean_data['asset_type'], self.clean_data['kinds'])

        obj = hashlib.md5()
        obj.update(unique_str)

        tmp_str = obj.hexdigest()[-4:].upper()
        self.asset_uid = self.clean_data['sn'] + '-00' + '%s' % ord(tmp_str[0]) + tmp_str[1:]
        self.asset_uid = obj.hexdigest().upper()
        return self.asset_uid


class Handler(DataValidityCheck):
    def data_incorporated(self):
        # if data_is_valid return True, then this func will be called.
        if self.data_validation:
            if self.agent_asset_uid == '0':
                self.create_method(self.clean_data['asset_type'])
            else:
                self.update_method(self.clean_data['asset_type'])

    def create_method(self, types):
        func = getattr(self, '_create_asset_%s' % types)
        func()

    def update_method(self, types):
        func = getattr(self, '_update_asset_%s' % types)
        func()

    def _create_asset_server(self):
        self.generate_asset_uid()
        if self.asset_uid is None:
            self.response_msg('error', '_create_asset_server', 'generate_asset_uid() failed.')
            return False

        self.__add_server_obj()
        self.__check_manufactory()
        self.__add_cpu_component()
        self.__add_disk_component()
        self.__add_nic_component()
        self.__add_ram_component()
        self.__add_os_component()

        # log_msg = "Asset [<a href='/admin/assets/asset/%s/' target='_blank'>%s</a>] has been created!" % (
        #     self.server_obj.uid, self.server_obj)
        # self.response_msg('info', 'NewAssetOnline', log_msg)

    def __add_server_obj(self, ignore_errs=False, only_check_sn=False):
        try:
            if models.Server.objects.filter(uid=self.asset_uid):
                self.response_msg('error', '__add_server_obj', u'资产uid已存在 %s' % self.asset_uid)
                print u'资产uid已存在 %s' % self.asset_uid

            self.field_verify(self.clean_data, 'model', str, mth='__add_server_obj')
            if not len(self.response['error']) or ignore_errs:  # no errors or ignore errors
                data_dic = {
                    'uid': self.asset_uid,
                    'sn': self.clean_data['sn'],
                    'model': self.clean_data.get('model'),
                    'hosted': self.clean_data.get('hosted'),
                }
                obj = models.Server(**data_dic)
                obj.save()

                log_msg = "Asset<%s> add new [server] record ." % self.asset_uid
                self.response_msg('info', '__add_server_obj', log_msg)

                self.add_successful = True

            if only_check_sn:
                self.server_obj = models.Server.objects.get(uid=self.asset_uid)
            else:
                self.server_obj = models.Server.objects.get(uid=self.asset_uid, sn=self.clean_data['sn'])

        except Exception, e:
            self.response_msg('error', '__add_server_obj', str(e))
            self.add_successful = False

    def __check_manufactory(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'manufactory', str, mth='__check_manufactory')
            manufactory = self.clean_data.get('manufactory')
            if not len(self.response['error']) or ignore_errs:
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

        except Exception, e:
            self.response_msg('error', '__check_manufactory', str(e))
            self.add_successful = False

    def __add_cpu_component(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'model', str, mth='__add_cpu_component')
            self.field_verify(self.clean_data, 'physical_count', int, mth='__add_cpu_component')
            self.field_verify(self.clean_data, 'logic_count', int, mth='__add_cpu_component')
            if not len(self.response['error']) or ignore_errs:
                data_set = {
                    'asset_uid': self.server_obj,
                    'cpu_model': self.clean_data.get('cpu_model'),
                    'physical_count': self.clean_data.get('physical_count'),
                    'logic_count': self.clean_data.get('logic_count'),
                }

                obj = models.CPU(**data_set)
                obj.save()

                log_msg = "Asset<%s> add new [cpu] record with data [%s]" % (self.asset_uid, data_set)
                self.response_msg('info', '__add_cpu_component', log_msg)

                self.add_successful = True

        except Exception, e:
            self.response_msg('error', '__add_cpu_component', str(e))
            self.add_successful = False

    def __add_disk_component(self):
        disk_info = self.clean_data.get('physical_disk_driver')
        if disk_info:
            for disk_item in disk_info:
                try:
                    if self.kinds == 'physics_machines':
                        self.field_verify(disk_item, 'slot', str, mth='__add_disk_component')
                        self.field_verify(disk_item, 'capacity', str, mth='__add_disk_component')
                        self.field_verify(disk_item, 'iface_type', str, mth='__add_disk_component')
                        self.field_verify(disk_item, 'model', str, mth='__add_disk_component')
                        if not len(self.response['error']):  # no processing when there's no error happend
                            data_set = {
                                'asset_uid': self.server_obj,
                                'sn': disk_item.get('sn'),
                                'slot': disk_item.get('slot'),
                                'capacity': disk_item.get('capacity'),
                                'model': disk_item.get('model'),
                                'iface_type': disk_item.get('iface_type'),
                                'manufactory': disk_item.get('manufactory'),
                            }

                            obj = models.Disk(**data_set)
                            obj.save()

                            log_msg = "Asset<%s> add new [disk] record with data [%s]" % (self.asset_uid, data_set)
                            self.response_msg('info', '__add_disk_component', log_msg)

                            self.add_successful = True

                    else:
                        if not len(self.response['error']):  # no processing when there's no error happend
                            data_set = {
                                'asset_uid': self.server_obj,
                                'capacity': disk_item.get('capacity'),
                            }

                            obj = models.Disk(**data_set)
                            obj.save()

                            log_msg = "Asset<%s> add new [disk] record with data [%s]" % (self.asset_uid, data_set)
                            self.response_msg('info', '__add_disk_component', log_msg)

                            self.add_successful = True

                except Exception, e:
                    self.response_msg('error', '__add_disk_component', str(e))
                    self.add_successful = False
        else:
            self.response_msg('error', '__add_disk_component', 'Disk info is not provied in your reporting data')
            self.add_successful = False

    def __add_nic_component(self):
        nic_info = self.clean_data.get('nic')
        if nic_info:
            for nic_item in nic_info:
                try:
                    self.field_verify(nic_item, 'mac', str)
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_uid': self.server_obj,
                            'name': nic_item.get('name'),
                            'sn': nic_item.get('sn'),
                            'mac': nic_item.get('mac'),
                            'ip': nic_item.get('ip'),
                            'bonding': nic_item.get('bonding'),
                            'model': nic_item.get('model'),
                            'mask': nic_item.get('mask'),
                        }

                        obj = models.NIC(**data_set)
                        obj.save()

                        log_msg = "Asset<%s> add new [nic] record with data [%s]" % (self.asset_uid, data_set)
                        self.response_msg('info', '__add_nic_component', log_msg)

                        self.add_successful = True

                except Exception, e:
                    self.response_msg('error', '__add_nic_component', str(e))
                    self.add_successful = False

        else:
            self.response_msg('error', '__add_nic_component', 'NIC info is not provied in your reporting data')
            self.add_successful = False

    def __add_ram_component(self):
        ram_info = self.clean_data.get('ram')
        if ram_info:
            for ram_item in ram_info:
                try:
                    if self.kinds == 'physics_machines':
                        self.field_verify(ram_item, 'capacity', str)
                        if not len(self.response['error']):  # no processing when there's no error happend
                            data_set = {
                                'asset_uid': self.server_obj,
                                'slot': ram_item.get("slot"),
                                'sn': ram_item.get('sn'),
                                'capacity': ram_item.get('capacity'),
                                'model': ram_item.get('model'),
                            }
                            obj = models.RAM(**data_set)
                            obj.save()

                            log_msg = "Asset<%s> add new [ram] record with data [%s]" % (self.asset_uid, data_set)
                            self.response_msg('info', '__add_ram_component', log_msg)

                            self.add_successful = True

                    else:
                        if not len(self.response['error']):
                            data_set = {
                                'asset_uid': self.server_obj,
                                'model': ram_item.get('model'),
                            }
                            obj = models.RAM(**data_set)
                            obj.save()

                            log_msg = "Asset<%s> add new [ram] record with data [%s]" % (self.asset_uid, data_set)
                            self.response_msg('info', '__add_ram_component', log_msg)

                            self.add_successful = True

                except Exception, e:
                    self.response_msg('error', '__add_ram_component', 'Object [ram] %s' % str(e))
                    self.add_successful = False

        else:
            self.response_msg('error', '__add_ram_component', 'RAM info is not provied in your reporting data')
            self.add_successful = False

    def __add_os_component(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'os_type', str)
            self.field_verify(self.clean_data, 'os_distribution', str)
            self.field_verify(self.clean_data, 'os_release', str)
            if not len(self.response['error']) or ignore_errs:
                data_set = {
                    'asset_uid': self.server_obj,
                    'os_type': self.clean_data.get('os_type'),
                    'os_distribution': self.clean_data.get('os_distribution'),
                    'os_release': self.clean_data.get('os_release'),
                }
                obj = models.OS(**data_set)
                obj.save()

                log_msg = "Asset<%s> add new [os] record with data [%s]" % (self.asset_uid, data_set)
                self.response_msg('info', '__add_os_component', log_msg)

                self.add_successful = True

        except Exception, e:
            self.response_msg('error', '__add_os_component', 'Object [os] %s' % str(e))
            self.add_successful = False

    def _update_asset_server(self):
        """ update server record according to data from agent """
        try:
            self.asset_uid = self.clean_data['asset_uid']

            self.__update_server_component()

            self.__update_asset_component(
                component_data=self.clean_data['nic'],
                fk='nic_set',
                update_fields=['sn', 'model', 'name', 'ip', 'mask', 'mac', 'bonding'],
                identify_field='mac'
            )

            self.__update_asset_component(
                component_data=self.clean_data['physical_disk_driver'],
                fk='disk_set',
                update_fields=['slot', 'sn', 'model', 'manufactory', 'capacity',
                               'iface_type'],
                identify_field='slot'
            )
            self.__update_asset_component(
                component_data=self.clean_data['ram'],
                fk='ram_set',
                update_fields=['slot', 'sn', 'model', 'capacity'],
                identify_field='slot'
            )
            # cpu = self.__update_cpu_component()
            # manufactory = self.__update_manufactory_component()
            self.update_successful = True

        except Exception, e:
            self.response_msg('error', '_update_asset_server', 'Object [server] %s' % str(e))
            self.update_successful = False

    def __update_server_component(self):
        update_fields = ['model', ]
        self.server_obj = models.Server.objects.get(uid=self.asset_uid)
        self.__compare_componet(model_obj=self.server_obj, update_fields=update_fields, data_source=self.clean_data)

    def __compare_componet(self, model_obj, update_fields, data_source):
        """
        :param model_obj: 需要进行对比的 model object
        :param update_fields:
        :param data_source:
        :return:
        """
        for field in update_fields:  # base on data in mysql
            val_from_db = getattr(model_obj, field)
            val_from_agent = data_source.get(field)
            if val_from_agent:
                if str(val_from_db) != str(val_from_agent):
                    # TODO: a special method, update data in mysql. # Retrieving a single field instance of a model by name
                    db_field_obj = model_obj._meta.get_field(field)
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

    def __update_asset_component(self, component_data, fk, update_fields, identify_field=None):
        """
        component_data: the specified component's data
        fk: which key to use to find the connection between main Asset obj and each asset component
        update_fields: what fields in DB will be compared and updated
        identify_field: identify each component of an Asset , None means only use asset id to identify
        """
        try:
            component_obj = getattr(self.server_obj, fk)  # 获取关联外键表对象
            if hasattr(component_obj, 'select_related'):  # component_obj is reverse m2m relation with server model
                objects_from_db = component_obj.select_related()
                for obj in objects_from_db:  # obj 每条匹配的row对象
                    field_data_from_db = getattr(obj, identify_field)  # To obtain the value of the specified fields

                    if type(component_data) is list:
                        for agent_data_item in component_data:
                            field_data_from_agent = agent_data_item.get(identify_field, 'none')
                            if field_data_from_agent:
                                if field_data_from_db == field_data_from_agent:
                                    self.__compare_componet(model_obj=obj, update_fields=update_fields,
                                                            data_source=agent_data_item)

                                    component_data.remove(agent_data_item)  # 把本次匹配到的记录删除，避免重复循环
                                    break
                            else:  # key field data from source data cannot be none
                                self.response_msg(
                                    'warning', '__update_asset_component',
                                    "Asset: table<%s> where uid = %s and %s = %s; Not provided in agent data " % (
                                        fk, self.server_obj.uid, identify_field, field_data_from_db))

                        else:  # couldn't find any matches, the asset component must be broken or changed manually
                            self.response_msg(
                                "error", "__update_asset_component",
                                "Cannot find any matches in agent data by key field val [%s]" % field_data_from_db)

                    elif type(component_data) is dict:  # dprecated...
                        for key, agent_data_item in component_data.items():
                            field_data_from_agent = agent_data_item.get(identify_field, 'none')
                            if field_data_from_agent:
                                if field_data_from_db == field_data_from_agent:
                                    self.__compare_componet(model_obj=obj, update_fields=update_fields,
                                                            data_source=agent_data_item)
                                    break
                            else:  # key field data from source data cannot be none
                                self.response_msg(
                                    'warning', '__update_asset_component',
                                    "Asset: table<%s> where uid = %s and %s = %s; Not provided in agent data " % (
                                        fk, self.server_obj.uid, identify_field, field_data_from_db))

                        else:  # couldn't find any matches, the asset component must be broken or changed manually
                            self.response_msg(
                                "error", "__update_asset_component",
                                "Cannot find any matches in agent data by key field val [%s]" % field_data_from_db)
                    else:
                        print '\033[31;1mMust be sth wrong,logic should goes to here at all.\033[0m'

            else:  # this component is reverse fk relation with Asset model
                pass
        except ValueError, e:
            print '\033[41;1m%s\033[0m' % str(e)

    def __filter_add_or_deleted_components(self, model_obj_name, data_from_db, data_source, identify_field):
        '''This function is filter out all  component data in db but missing in reporting data, and all the data in reporting data but not in DB'''
        print data_from_db, data_source, identify_field
        data_source_key_list = []  # save all the idenified keys from client data,e.g: [macaddress1,macaddress2]
        if type(data_source) is list:
            for data in data_source:
                data_source_key_list.append(data.get(identify_field))
        elif type(data_source) is dict:  # dprecated
            for key, data in data_source.items():
                if data.get(identify_field):
                    data_source_key_list.append(data.get(identify_field))
                else:  # workround for some component uses key as identified field e.g: ram
                    data_source_key_list.append(key)
        print '-->identify field [%s] from db  :', data_source_key_list
        print '-->identify[%s] from data source:', [getattr(obj, identify_field) for obj in data_from_db]

        data_source_key_list = set(data_source_key_list)
        data_identify_val_from_db = set([getattr(obj, identify_field) for obj in data_from_db])
        data_only_in_db = data_identify_val_from_db - data_source_key_list  # delete all this from db
        data_only_in_data_source = data_source_key_list - data_identify_val_from_db  # add into db
        print '\033[31;1mdata_only_in_db:\033[0m', data_only_in_db
        print '\033[31;1mdata_only_in_data source:\033[0m', data_only_in_data_source
        self.__delete_components(all_components=data_from_db, delete_list=data_only_in_db,
                                 identify_field=identify_field)
        if data_only_in_data_source:
            self.__add_components(model_obj_name=model_obj_name, all_components=data_source,
                                  add_list=data_only_in_data_source, identify_field=identify_field)


def log_handler(server_obj, event_name, user, detail, component=None):
    if not user.id:
        user = UserProfile.objects.filter(is_admin=True).last()

    try:
        log_obj = models.EventLog(
            asset_uid=server_obj,
            event_name=event_name,
            user_id=user.id,
            detail=detail,
            component=component,
            memo=server_obj.uid)

        log_obj.save()
        return True
    except Exception, e:
        print e
        return False
