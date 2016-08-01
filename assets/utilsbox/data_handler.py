# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
import json
from assets import models
from django.core.exceptions import ObjectDoesNotExist


class DataValidityCheck(object):
    def __init__(self, request):
        self.request = request
        self.mandatory_fields = ['sn', 'asset_id', 'asset_type']
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
        self.agent_asset_id = None
        self.asset_obj = None

    def data_is_valid(self):
        # self.request.data --> QueryDict
        data = self.request.data.get("asset_data")  # unicode
        if data:
            try:
                data = json.loads(data)
                print(__file__, type(data), data)
                self.mandatory_check(data)
                self.clean_data = data
                self.agent_asset_id = int(data['asset_id'])
                if not self.response['error']:
                    return True
            except ValueError, e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
                return False
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")
        return False

    def response_msg(self, msg_type, key, msg):
        if msg_type in self.response:
            self.response[msg_type].append({key: msg})
        else:
            raise ValueError

    # 检查必须项
    def mandatory_check(self, data, only_check_sn=False):
        for field in self.mandatory_fields:
            if field not in data:
                self.response_msg(
                    'error',
                    'MandatoryCheckFailed',
                    "Can not find [%s] in your reporting data" % field)
        else:
            if self.response['error']:
                return False
        try:
            if self.agent_asset_id != 0:  # not new asset
                if only_check_sn:
                    self.asset_obj = models.Asset.objects.get(sn=data['sn'])
                else:
                    self.asset_obj = models.Asset.objects.get(id=int(data['asset_id']), sn=data['sn'])
            else:  # new asset
                pass

        except ObjectDoesNotExist, e:
            self.response_msg(
                'error',
                'AssetDataInvalid',
                "Cannot find asset object by asset id [%s] and SN [%s] " % (data['asset_id'], data['sn']))
            self.waiting_approval = True
            return False

    def asset_type_existing(self):
        if not hasattr(self.asset_obj, self.clean_data['asset_type']):
            return True
        else:
            return False

    def field_verify(self, data_set, field_key, data_type, required=True):
        field_val = data_set.get(field_key)  # "model": "Latitude 3330"
        if field_val:
            try:
                data_set[field_key] = data_type(field_val)
            except ValueError, e:
                self.response_msg(
                    'error',
                    'InvalidField',
                    "The field [%s]'s data type is invalid, the correct data type should be [%s] " % (
                        field_key, data_type))

        elif required:
            self.response_msg(
                'error',
                'LackOfField',
                "The field [%s] has no value provided in your reporting data [%s]" % (
                    field_key, data_set))

    @property
    def generate_asset_id(self):
        pass
        return 0


class Handler(DataValidityCheck):
    def data_incorporated(self):
        # if data_is_valid return True, then this func will be called.
        if self.agent_asset_id() == 0:
            self.create_asset()
        else:
            self.update_asset()

    # create new asset (type: server)
    def create_asset(self):
        func = getattr(self, '_create_asset_%s' % self.clean_data['asset_type'])
        func()

    # update asset msg
    def update_asset(self):
        func = getattr(self, '_update_%s' % self.clean_data['asset_type'])
        func()

    def _create_asset_server(self):
        self.__create_server_info()
        self.__create_or_update_manufactory()
        self.__create_cpu_component()
        self.__create_disk_component()
        self.__create_nic_component()
        self.__create_ram_component()

        log_msg = "Asset [<a href='/admin/assets/asset/%s/' target='_blank'>%s</a>] has been created!" % (
            self.asset_obj.id, self.asset_obj)
        self.response_msg('info', 'NewAssetOnline', log_msg)

    def __create_server_info(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'model', str)
            if not len(self.response['error']) or ignore_errs:  # no errors or ignore errors
                data_set = {
                    'asset_id': self.generate_asset_id,
                    'raid_type': self.clean_data.get('raid_type'),
                    'model': self.clean_data.get('model'),
                    'os_type': self.clean_data.get('os_type'),
                    'os_distribution': self.clean_data.get('os_distribution'),
                    'os_release': self.clean_data.get('os_release'),
                }

                obj = models.Server(**data_set)
                obj.save()
                return obj
        except Exception, e:
            self.response_msg('error', 'ObjectCreationException', 'Object [server] %s' % str(e))

    def __create_or_update_manufactory(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'manufactory', str)
            manufactory = self.clean_data.get('manufactory')
            if not len(self.response['error']) or ignore_errs:
                obj_exist = models.Manufactory.objects.filter(manufactory=manufactory)
                if obj_exist:
                    obj = obj_exist[0]
                else:  # create a new one
                    obj = models.Manufactory(manufactory=manufactory)
                    obj.save()
                self.asset_obj.manufactory = obj
                self.asset_obj.save()
        except Exception, e:
            self.response_msg('error', 'ObjectCreationException', 'Object [manufactory] %s' % str(e))

    def __create_cpu_component(self, ignore_errs=False):
        try:
            self.field_verify(self.clean_data, 'model', str)
            self.field_verify(self.clean_data, 'cpu_count', int)
            self.field_verify(self.clean_data, 'cpu_core_count', int)
            if not len(self.response['error']) or ignore_errs:  # no processing when there's no error happend
                data_set = {
                    'asset_id': self.generate_asset_id,
                    'cpu_model': self.clean_data.get('cpu_model'),
                    'cpu_count': self.clean_data.get('cpu_count'),
                    'cpu_core_count': self.clean_data.get('cpu_core_count'),
                }

                obj = models.CPU(**data_set)
                obj.save()
                log_msg = "Asset[%s] --> has added new [cpu] component with data [%s]" % (self.asset_obj, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                return obj
        except Exception, e:
            self.response_msg('error', 'ObjectCreationException', 'Object [cpu] %s' % str(e))

    def _update_server(self):
        nic = self.__update_asset_component(
            data_source=self.clean_data['nic'],
            fk='nic_set',
            update_fields=['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask',
                           'bonding'],
            identify_field='macaddress'
        )
        disk = self.__update_asset_component(data_source=self.clean_data['physical_disk_driver'],
                                             fk='disk_set',
                                             update_fields=['slot', 'sn', 'model', 'manufactory', 'capacity',
                                                            'iface_type'],
                                             identify_field='slot'
                                             )
        ram = self.__update_asset_component(data_source=self.clean_data['ram'],
                                            fk='ram_set',
                                            update_fields=['slot', 'sn', 'model', 'capacity'],
                                            identify_field='slot'
                                            )
        cpu = self.__update_cpu_component()
        manufactory = self.__update_manufactory_component()

        server = self.__update_server_component()
