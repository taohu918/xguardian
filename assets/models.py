# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
from __future__ import unicode_literals

from django.db import models
from userauth.models import UserProfile
import datetime


# Create your models here.
class Business(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=50, verbose_name='业务线')
    server_number = models.IntegerField(blank=True, null=True, verbose_name='服务器数量')
    memo = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'业务线'
        verbose_name_plural = u"业务线"


class IDC(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=50, verbose_name=u'机房名称')
    area = models.CharField(max_length=50, blank=True, null=True, verbose_name='所在地')
    tel = models.IntegerField(blank=True, null=True, verbose_name='联系电话')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'机房'
        verbose_name_plural = u"机房"


class Contract(models.Model):
    id = models.IntegerField(primary_key=True)
    sn = models.CharField(unique=True, max_length=50, verbose_name=u'合同号')
    name = models.CharField(max_length=50, verbose_name=u'合同名称')
    license_num = models.IntegerField(blank=True, null=True, verbose_name=u'license数量')
    memo = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'备注')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = u'合同'
        verbose_name_plural = u"合同"

    def __unicode__(self):
        return self.name


class Manufactory(models.Model):
    manufactory = models.CharField(max_length=50, verbose_name=u'厂商名称')
    support_num = models.IntegerField(blank=True, null=True, verbose_name=u'支持电话')
    memo = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'备注')

    def __unicode__(self):
        return self.manufactory

    class Meta:
        verbose_name = u'厂商'
        verbose_name_plural = u"厂商"


class Tag(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=50, verbose_name='Tag name')
    creater = models.ForeignKey('userauth.UserProfile', db_column='creater', verbose_name='创建者')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name


class Server(models.Model):
    created_by_choices = (
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    )
    uid = models.CharField(primary_key=True, max_length=50)
    sn = models.CharField(max_length=50)
    name = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)

    manufactory = models.ForeignKey('Manufactory', blank=True, null=True)
    business = models.ForeignKey('Business', blank=True, null=True, verbose_name=u'业务')
    idc = models.ForeignKey('IDC', blank=True, null=True, verbose_name=u'机房')
    contract = models.ForeignKey('Contract', blank=True, null=True, verbose_name=u'合同')
    admin = models.ForeignKey('userauth.UserProfile', blank=True, null=True, verbose_name=u'管理员')

    mip = models.CharField(max_length=50, blank=True, null=True)
    hosted_on = models.GenericIPAddressField(blank=True, null=True, verbose_name='虚拟底层')
    expired_date = models.DateField(blank=True, null=True, verbose_name='过保日期')
    create_time = models.DateTimeField(blank=True, auto_now_add=True)
    update_time = models.DateTimeField(blank=True, null=True, auto_now=True)

    class Meta:
        verbose_name = '服务器'
        verbose_name_plural = "服务器"

    def __unicode__(self):
        return '%s sn:%s' % (self.name, self.sn)


class TagAsset(models.Model):
    server_uid = models.ForeignKey('Server')
    tag_id = models.ForeignKey('Tag')

    class Meta:
        db_table = 'assets_server_tag'


class OS(models.Model):
    os_types_choice = (
        ('linux', 'Linux'),
        ('windows', 'Windows'))
    model_types_choices = (
        ('windows', 'Windows'),
        ('centos', 'CentOS'),
        ('ubuntu', 'Ubuntu'))
    uid = models.CharField(primary_key=True, max_length=50)
    os = models.CharField(choices=os_types_choice, max_length=50, default=1, verbose_name=u'系统类型')
    model = models.CharField(choices=model_types_choices, max_length=50, default=1, verbose_name=u'软件/系统版本')
    distribution = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return self.version

    class Meta:
        verbose_name = '系统'
        verbose_name_plural = "系统"


class CPU(models.Model):
    asset_uid = models.OneToOneField('Server', unique=True)
    cpu_model = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'CPU型号')
    physical_count = models.SmallIntegerField(u'物理cpu颗数')
    logic_count = models.SmallIntegerField(u'逻辑cpu核数')
    create_time = models.DateTimeField(blank=True, auto_now_add=True)
    update_time = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        verbose_name = 'CPU部件'
        verbose_name_plural = "CPU部件"

    def __unicode__(self):
        return self.cpu_model


class RAM(models.Model):
    asset_uid = models.ForeignKey('Server')
    sn = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'SN号')
    model = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'内存型号')
    slot = models.IntegerField(u'插槽', blank=True, null=True)
    capacity = models.IntegerField(u'内存大小(MB)', blank=True, null=True)
    memo = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'备注')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s:%s:%s' % (self.uid, self.slot, self.capacity)

    class Meta:
        verbose_name = 'RAM'
        verbose_name_plural = "RAM"

    auto_create_fields = ['sn', 'slot', 'model', 'capacity']


class Disk(models.Model):
    disk_iface_choice = (
        ('SATA', 'SATA'),
        ('SAS', 'SAS'),
        ('SCSI', 'SCSI'),
        ('SSD', 'SSD'),
    )
    uid = models.ForeignKey('Server', db_column='uid')
    sn = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'SN号')
    model = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'磁盘型号')
    slot = models.CharField(max_length=50, blank=True, null=True, verbose_name='插槽位')
    capacity = models.CharField(max_length=50, blank=True, null=True, verbose_name='磁盘容量GB')
    manufactory = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'制造商')
    iface_type = models.CharField(max_length=16, choices=disk_iface_choice, default='SAS', verbose_name=u'接口类型')
    create_time = models.DateTimeField(blank=True, auto_now_add=True)
    update_time = models.DateTimeField(blank=True, auto_now=True)

    auto_create_fields = ['sn', 'slot', 'manufactory', 'model', 'capacity', 'iface_type']

    class Meta:
        # unique_together = ("asset", "slot")
        verbose_name = '硬盘'
        verbose_name_plural = "硬盘"

    def __unicode__(self):
        return '%s:slot:%s capacity:%s' % (self.uid, self.slot, self.capacity)


class NIC(models.Model):
    uid = models.ForeignKey('Server', db_column='uid')
    sn = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'网卡型号')
    name = models.CharField(max_length=50, blank=True, null=True, verbose_name=u'网卡名')
    ip = models.GenericIPAddressField(max_length=32, blank=True, null=True)
    mask = models.GenericIPAddressField(max_length=32, blank=True, null=True)
    mac = models.CharField(max_length=32, unique=True, verbose_name=u'MAC')
    bonding = models.CharField(max_length=8, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s:%s' % (self.uid, self.mac)

    class Meta:
        verbose_name = u'网卡'
        verbose_name_plural = u"网卡"
        # unique_together = ("asset_id", "slot")

    auto_create_fields = ['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask', 'bonding']


class EventLog(models.Model):
    event_type_choices = (
        (1, u'硬件变更'),
        (2, u'新增配件'),
        (3, u'设备下线'),
        (4, u'设备上线'),
        (5, u'定期维护'),
        (6, u'业务上线\更新\变更'),
        (7, u'其它'),
    )
    uid = models.ForeignKey('Server', db_column='uid')
    user = models.ForeignKey('userauth.UserProfile', verbose_name=u'事件源')
    name = models.CharField(max_length=128, verbose_name=u'事件名称')

    event_type = models.SmallIntegerField(u'事件类型', choices=event_type_choices)
    component = models.CharField(max_length=255, blank=True, null=True, verbose_name='事件子项')
    detail = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'事件详情')
    memo = models.CharField(max_length=255, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = '事件纪录'
        verbose_name_plural = "事件纪录"

    def colored_event_type(self):
        if self.event_type == 1:
            cell_html = '<span style="background: orange;">%s</span>'
        elif self.event_type == 2:
            cell_html = '<span style="background: yellowgreen;">%s</span>'
        else:
            cell_html = '<span >%s</span>'
        return cell_html % self.get_event_type_display()

    colored_event_type.allow_tags = True
    colored_event_type.short_description = u'事件类型'
