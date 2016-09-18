# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import json
from assets import models
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist


class DataValidityCheck(object):
    def __init__(self, request):
        self.request = request
        self.mandatory_fields = ['sn', 'asset_uid', 'asset_type', 'kinds']
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
        self.agent_asset_uid = None
        self.asset_obj = None
        self.asset_uid = None
        self.add_successful = False
        self.update_successful = False

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
                if not self.response['error']:
                    return True
            except ValueError, e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
                return False
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")
        return False

    def mandatory_check(self, data):
        for field in self.mandatory_fields:
            if field not in data:
                self.response_msg(
                    'error',
                    'MandatoryCheckFailed',
                    "Can not find [%s] in your reporting data" % field)
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
        if not hasattr(self.asset_obj, self.clean_data['asset_type']):
            return True
        else:
            return False

    def field_verify(self, data_set, field_key, data_type, required=True):
        field_val = data_set.get(field_key)  # "model": "Latitude 3330"
        if field_val or field_val == 0:
            try:
                data_set[field_key] = data_type(field_val)
            except ValueError, e:
                self.response_msg(
                    'error',
                    'InvalidField',
                    "The field [%s]'s data type is invalid, the correct data type should be [%s] " % (
                        field_key, data_type))
                return False

        elif required:
            self.response_msg(
                'error',
                'LackOfField',
                "The field [%s] has no value provided in your reporting data [%s]" % (
                    field_key, data_set))
            return False

    def generate_asset_uid(self):
        import hashlib
        unique_str = "%s%s%s" % (self.clean_data['sn'], self.clean_data['asset_type'], self.clean_data['kinds'])

        obj = hashlib.md5()
        obj.update(unique_str)

        tmp_str = obj.hexdigest()[-4:].upper()
        self.asset_uid = self.clean_data['sn'] + '-00' + '%s' % ord(tmp_str[0]) + tmp_str[1:]

        return self.asset_uid


class Handler(DataValidityCheck):
    def data_incorporated(self):
        # if data_is_valid return True, then this func will be called.
        if self.agent_asset_uid == '0':
            self.create_method(self.clean_data['asset_type'])
        else:
            self.update_method(self.clean_data['asset_type'])

    # create new asset (type: server)
    def create_method(self, types):
        func = getattr(self, '_create_asset_%s' % types)
        func()

    # update asset server
    def update_method(self, types):
        func = getattr(self, '_update_asset_%s' % types)
        func()

    def _create_asset_server(self):
        self.generate_asset_uid()
        if self.asset_uid is None:
            self.response_msg('error', 'AssetUidInvalid', 'generate asset id is invalid ! ')
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
            self.field_verify(self.clean_data, 'model', str)
            if not len(self.response['error']) or ignore_errs:  # no errors or ignore errors
                data_dic = {
                    'uid': self.asset_uid,
                    'sn': self.clean_data['sn'],
                    'model': self.clean_data.get('model'),
                }
                obj = models.Server(**data_dic)
                obj.save()
                self.add_successful = True

            if only_check_sn:
                self.asset_obj = models.Server.objects.get(uid=self.asset_uid)
            else:
                self.asset_obj = models.Server.objects.get(uid=self.asset_uid, sn=self.clean_data['sn'])

        except Exception, e:
            self.response_msg('error', 'ObjectCreationException', '__add_server_obj: Object [server] %s' % str(e))
            self.add_successful = False

    def __check_manufactory(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'manufactory', str)
            manufactory = self.clean_data.get('manufactory')
            if not len(self.response['error']) or ignore_errs:
                obj = models.Manufactory.objects.filter(manufactory=manufactory)
                if obj:
                    this_obj = obj[0]
                else:
                    this_obj = models.Manufactory(manufactory=manufactory)
                    this_obj.save()
                self.asset_obj.manufactory = this_obj
                self.asset_obj.save()
                self.add_successful = True

        except Exception, e:
            self.response_msg('error', 'ObjectCreationException',
                              '__check_manufactory: Object [manufactory] %s' % str(e))
            self.add_successful = False

    def __add_cpu_component(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'model', str)
            self.field_verify(self.clean_data, 'physical_count', int)
            self.field_verify(self.clean_data, 'logic_count', int)
            if not len(self.response['error']) or ignore_errs:  # no processing when there's no error happend
                data_set = {
                    'asset_uid': self.asset_obj,
                    'cpu_model': self.clean_data.get('cpu_model'),
                    'physical_count': self.clean_data.get('physical_count'),
                    'logic_count': self.clean_data.get('logic_count'),
                }

                obj = models.CPU(**data_set)
                obj.save()
                log_msg = "Asset[%s] --> has added new [cpu] component with data [%s]" % (self.asset_obj, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                self.add_successful = True

        except Exception, e:
            self.response_msg('error', 'ObjectCreationException', '__add_cpu_component: Object [cpu] %s' % str(e))
            self.add_successful = False

    def __add_disk_component(self):
        disk_info = self.clean_data.get('physical_disk_driver')
        if disk_info:
            for disk_item in disk_info:
                try:
                    self.field_verify(disk_item, 'slot', str)
                    self.field_verify(disk_item, 'capacity', float)
                    self.field_verify(disk_item, 'iface_type', str)
                    self.field_verify(disk_item, 'model', str)
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_uid': self.asset_obj,
                            'sn': disk_item.get('sn'),
                            'slot': disk_item.get('slot'),
                            'capacity': disk_item.get('capacity'),
                            'model': disk_item.get('model'),
                            'iface_type': disk_item.get('iface_type'),
                            'manufactory': disk_item.get('manufactory'),
                        }

                        obj = models.Disk(**data_set)
                        obj.save()
                        self.add_successful = True

                except Exception, e:
                    self.response_msg('error', 'ObjectCreationException',
                                      '__add_disk_component: Object [disk] %s' % str(e))
                    self.add_successful = False
        else:
            self.response_msg('error', 'LackOfData', 'Disk info is not provied in your reporting data')
            self.add_successful = False

    def __add_nic_component(self):
        nic_info = self.clean_data.get('nic')
        if nic_info:
            for nic_item in nic_info:
                try:
                    self.field_verify(nic_item, 'mac', str)
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_uid': self.asset_obj,
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
                        self.add_successful = True

                except Exception, e:
                    self.response_msg('error', 'ObjectCreationException',
                                      '__add_nic_component: Object [nic] %s' % str(e))
                    self.add_successful = False

        else:
            self.response_msg('error', 'LackOfData', 'NIC info is not provied in your reporting data')
            self.add_successful = False

    def __add_ram_component(self):
        ram_info = self.clean_data.get('ram')
        if ram_info:
            for ram_item in ram_info:
                try:
                    self.field_verify(ram_item, 'capacity', int)
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_uid': self.asset_obj,
                            'slot': ram_item.get("slot"),
                            'sn': ram_item.get('sn'),
                            'capacity': ram_item.get('capacity'),
                            'model': ram_item.get('model'),
                        }

                        obj = models.RAM(**data_set)
                        obj.save()
                        self.add_successful = True

                except Exception, e:
                    self.response_msg('error', 'ObjectCreationException',
                                      '__add_ram_component: Object [ram] %s' % str(e))
                    self.add_successful = False

        else:
            self.response_msg('error', 'LackOfData', 'RAM info is not provied in your reporting data')
            self.add_successful = False

    def __add_os_component(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'os_type', str)
            self.field_verify(self.clean_data, 'os_distribution', str)
            self.field_verify(self.clean_data, 'os_release', str)
            if not len(self.response['error']) or ignore_errs:
                data_set = {
                    'asset_uid': self.asset_obj,
                    'os_type': self.clean_data.get('os_type'),
                    'os_distribution': self.clean_data.get('os_distribution'),
                    'os_release': self.clean_data.get('os_release'),
                }
                obj = models.OS(**data_set)
                obj.save()
                log_msg = "Asset[%s] --> has added new [os] component with data [%s]" % (self.asset_obj, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                self.add_successful = True

        except Exception, e:
            self.response_msg('error', 'ObjectCreationException', '__add_os_component: Object [os] %s' % str(e))
            self.add_successful = False

    def _update_asset_server(self):
        """ update server record according to data from agent """
        try:
            self.asset_uid = self.clean_data['asset_uid']

            self.__update_server_component()

            self.__update_asset_component(
                component_data=self.clean_data['nic'],
                fk='nic_set',
                update_fields=['name', 'sn', 'model', 'mac', 'ip', 'mask', 'bonding'],
                identify_field='mac'
            )

            """
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
            cpu = self.__update_cpu_component()
            manufactory = self.__update_manufactory_component()"""
            self.update_successful = True

        except Exception, e:
            self.response_msg('error', 'ObjectCreationException', '_update_asset_server: Object [server] %s' % str(e))
            self.update_successful = False

    def __update_server_component(self):
        update_fields = ['model', ]
        self.asset_obj = models.Server.objects.get(uid=self.asset_uid)
        self.__compare_componet(model_obj=self.asset_obj, update_fields=update_fields, data_source=self.clean_data)

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
                    # TODO: a special method, update data in mysql.
                    db_field_obj = model_obj._meta.get_field(field)
                    db_field_obj.save_form_data(model_obj, val_from_agent)
                    model_obj.update_date = timezone.now()
                    model_obj.save()

                    log_msg = u"Table<%s> Field<%s> Changed: From '%s' to '%s' " % (
                        'Server', field, val_from_db, val_from_agent)
                    self.response_msg('info', 'FieldChanged', log_msg)
                    log_handler(self.asset_obj, 'FieldChanged', self.request.user, log_msg)
                    self.update_successful = True
            else:
                self.response_msg(
                    'warning', 'AssetUpdateWarning',
                    "Asset component [%s]'s field [%s] is not provided in reporting data " % (
                        model_obj, field))

                # model_obj.save()

    def __update_asset_component(self, component_data, fk, update_fields, identify_field=None):
        """
        component_data: the specified component's data
        fk: which key to use to find the connection between main Asset obj and each asset component
        update_fields: what fields in DB will be compared and updated
        identify_field: identify each component of an Asset , None means only use asset id to identify
        """
        try:
            component_obj = getattr(self.asset_obj, fk)  # 获取关联外键表对象
            if hasattr(component_obj, 'select_related'):  # component_obj is reverse m2m relation with server model
                objects_from_db = component_obj.select_related()
                for obj in objects_from_db:  # obj 每条匹配的row对象
                    key_field_data = getattr(obj, identify_field)

                    if type(component_data) is list:
                        for agent_data_item in component_data:
                            key_field_data_from_agent_data = agent_data_item.get(identify_field, 'none')
                            if key_field_data_from_agent_data:
                                if key_field_data == key_field_data_from_agent_data:
                                    self.__compare_componet(
                                        model_obj=obj,
                                        update_fields=update_fields,
                                        data_source=agent_data_item)
                                    break
                                    # break here, or logic will goes for ..else part when the loop is finished,
                                    # then you will know that no agent data is matched for by using this key_field_data
                                    # means that item is lacked from agent data (makes sense when hardware info got changed)
                                    # e.g: one of the RAM is broken, sb takes it away, then this data will not be reported

                            else:  # key field data from source data cannot be none
                                self.response_msg(
                                    'warning', 'AssetUpdateWarning',
                                    "Asset component [%s]'s key field [%s] is not provided in reporting data " % (
                                        fk, identify_field))

                        else:  # couldn't find any matches, the asset component must be broken or changed manually
                            self.response_msg(
                                "error", "AssetUpdateWarning",
                                "Cannot find any matches in agent data by key field val [%s]" % key_field_data)

                    elif type(component_data) is dict:  # dprecated...
                        for key, agent_data_item in component_data.items():
                            key_field_data_from_source_data = agent_data_item.get(identify_field)
                            if key_field_data_from_source_data:
                                if key_field_data == key_field_data_from_source_data:  # find the matched source data for this component,then should compare each field in this component to see if there's any changes since last update
                                    self.__compare_componet(model_obj=obj, fields_from_db=update_fields,
                                                            source_data=agent_data_item)
                                    break  # must break ast last ,then if the loop is finished , logic will goes for ..else part,then you will know that no source data is matched for by using this key_field_data, that means , this item is lacked from source data, it makes sense when the hardware info got changed. e.g: one of the RAM is broken, sb takes it away,then this data will not be reported in reporting data
                            else:  # key field data from source data cannot be none
                                self.response_msg('warning', 'AssetUpdateWarning',
                                                  "Asset component [%s]'s key field [%s] is not provided in reporting data " % (
                                                      fk, identify_field))

                        else:  # couldn't find any matches, the asset component must be broken or changed manually
                            print '\033[33;1mWarning:cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!\033[0m' % (
                                key_field_data)
                    else:
                        print '\033[31;1mMust be sth wrong,logic should goes to here at all.\033[0m'
                        # compare all the components from DB with the data source from reporting data
                        # self.__filter_add_or_deleted_components(model_obj_name=component_obj.model._meta.object_name,
                        #                                         data_from_db=objects_from_db, data_source=component_data,
                        #                                         identify_field=identify_field)

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


def log_handler(asset_obj, event_name, user, detail, component=None):
    if not user.id:
        user = models.UserProfile.objects.filter(is_admin=True).last()

    try:
        log_obj = models.EventLog(
            asset_uid=asset_obj,
            event_name=event_name,
            user_id=user.id,
            detail=detail,
            component=component,
            memo=asset_obj.uid)

        log_obj.save()
        return True
    except Exception, e:
        print e
        return False
