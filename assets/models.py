# -*- coding: utf-8 -*-
# __author__: taohu

# import sys
# reload(sys)
# sys.setdefaultencoding("utf-8")
from __future__ import unicode_literals

from django.db import models
from userauth.models import UserProfile


# Create your models here.
class BusinessUnit(models.Model):
    name = models.CharField(unique=True, max_length=64, verbose_name='业务线')
    parent_unit = models.ForeignKey('self', db_column='parent_unit', blank=True, null=True, verbose_name='子业务')
    memo = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'业务线'
        verbose_name_plural = u"业务线"


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=64, verbose_name='Tag name')
    creater = models.ForeignKey('userauth.UserProfile', db_column='creater', verbose_name='创建者')
    create_time = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return self.name


class IDC(models.Model):
    name = models.CharField(unique=True, max_length=64, verbose_name=u'机房名称')
    memo = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = u'机房'
        verbose_name_plural = u"机房"


class Manufactory(models.Model):
    manufactory = models.CharField(unique=True, max_length=64, verbose_name=u'厂商名称')
    support_num = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'支持电话')
    memo = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'备注')

    def __unicode__(self):
        return self.manufactory

    class Meta:
        verbose_name = u'厂商'
        verbose_name_plural = u"厂商"


class Contract(models.Model):
    sn = models.CharField(unique=True, max_length=64, verbose_name=u'合同号')
    name = models.CharField(max_length=64, verbose_name=u'合同名称')
    price = models.FloatField(verbose_name=u'合同金额')
    start_date = models.DateField(blank=True)
    end_date = models.DateField(blank=True)
    license_num = models.IntegerField(blank=True, verbose_name=u'license数量')
    detail = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'合同详细')
    memo = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'备注')
    create_time = models.DateField(auto_now_add=True)
    update_time = models.DateField(auto_now=True)

    class Meta:
        verbose_name = u'合同'
        verbose_name_plural = u"合同"

    def __unicode__(self):
        return self.name


class Asset(models.Model):
    asset_type_choices = (
        ('server', u'服务器'),
        ('switch', u'交换机'),
        ('router', u'路由器'),
        ('firewall', u'防火墙'),
        ('storage', u'存储设备'),
        ('NLB', u'NetScaler'),
        ('wireless', u'无线AP'),
        ('software', u'软件资产'),
        ('others', u'其它类'),
    )
    uid = models.CharField(primary_key=True, max_length=64, verbose_name='资产唯一id')
    sn = models.CharField(unique=True, max_length=64, verbose_name=u'资产SN号')
    name = models.CharField(unique=True, max_length=64)

    admin = models.ForeignKey('userauth.UserProfile', db_column='admin', blank=True, null=True)
    business_unit = models.ForeignKey('BusinessUnit', db_column='business_unit', blank=True, null=True)
    idc = models.ForeignKey('IDC', db_column='idc', blank=True, null=True)
    manufactory = models.ForeignKey('Manufactory', db_column='manufactory', blank=True, null=True)
    contract = models.ForeignKey('Contract', db_column='contract', blank=True, null=True)
    tag = models.ManyToManyField('Tag', through='TagAsset')

    management_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name=u'管理IP')
    asset_type = models.CharField(choices=asset_type_choices, max_length=64, default='server')
    trade_date = models.DateField(blank=True, null=True, verbose_name=u'购买时间')
    expire_date = models.DateField(blank=True, null=True, verbose_name=u'过保时间', )
    price = models.FloatField(blank=True, null=True, verbose_name=u'价格')

    memo = models.CharField(max_length=255, blank=True, null=True)
    create_time = models.DateTimeField(blank=True, auto_now_add=True)
    update_time = models.DateTimeField(blank=True, auto_now=True)

    class Meta:
        verbose_name = '资产明细表'
        verbose_name_plural = "资产明细表"

    def __unicode__(self):
        return 'id:%s name:%s' % (self.uid, self.name)


class TagAsset(models.Model):
    asset_uid = models.ForeignKey('Asset')
    tag_id = models.ForeignKey('Tag')

    class Meta:
        db_table = 'assets_tag_asset'


class Server(models.Model):
    created_by_choices = (
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    )

    asset = models.OneToOneField('Asset', db_column='asset')
    model = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'型号')
    raid_type = models.CharField(max_length=16, blank=True, null=True, verbose_name=u'raid类型')
    os_type = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'操作系统类型')
    os_distribution = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'发型版本')
    os_release = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'操作系统版本')

    hosted_on = models.ForeignKey('self', db_column='hosted_on', blank=True, null=True)  # for vitural server
    created_by = models.CharField(choices=created_by_choices, max_length=16, default='auto')
    approved_by = models.ForeignKey('userauth.UserProfile', db_column='approved_by', blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '服务器'
        verbose_name_plural = "服务器"

    def __unicode__(self):
        return '%s sn:%s' % (self.asset.name, self.asset.sn)


class Platform(models.Model):
    os_types_choice = (
        ('linux', 'Linux'),
        ('windows', 'Windows'),
        ('firmware', 'Network Firmware'),
        ('software', 'Softwares'),)
    os_distribution_choices = (
        ('windows', 'Windows'),
        ('centos', 'CentOS'),
        ('ubuntu', 'Ubuntu'))
    language_choices = (
        ('cn', u'中文'),
        ('en', u'英文'))
    type = models.CharField(choices=os_types_choice, max_length=32, default=1, verbose_name=u'系统类型')
    version = models.CharField(unique=True, max_length=32, verbose_name=u'软件/系统版本')
    language = models.CharField(choices=language_choices, default='cn', max_length=16)
    memo = models.CharField(max_length=255)

    def __unicode__(self):
        return self.version

    class Meta:
        verbose_name = '软件/系统'
        verbose_name_plural = "软件/系统"


class NetDevice(models.Model):
    asset = models.OneToOneField('Asset', db_column='asset')
    sn = models.CharField(unique=True, max_length=64, verbose_name=u'SN号')
    vlan_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name=u'VlanIP')
    intranet_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name=u'内网IP')

    model = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'型号')
    firmware = models.ForeignKey('Platform', db_column='firmware', blank=True, null=True)
    port_count = models.SmallIntegerField(blank=True, null=True, verbose_name=u'端口个数')
    device_detail = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'设置详细配置')
    creat_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = u'网络设备'
        verbose_name_plural = u"网络设备"


class CPU(models.Model):
    asset = models.OneToOneField('Asset', db_column='asset')
    cpu_model = models.CharField(max_length=64, blank=True, verbose_name=u'CPU型号')
    cpu_count = models.SmallIntegerField(u'物理cpu颗数')
    cpu_core_count = models.SmallIntegerField(u'cpu核数')
    memo = models.CharField(u'备注', max_length=255, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CPU部件'
        verbose_name_plural = "CPU部件"

    def __unicode__(self):
        return self.cpu_model


class RAM(models.Model):
    asset = models.ForeignKey('Asset', db_column='asset')
    sn = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'SN号')
    model = models.CharField(max_length=128, verbose_name=u'内存型号')
    slot = models.SmallIntegerField(u'插槽')
    capacity = models.IntegerField(u'内存大小(MB)')
    memo = models.CharField(max_length=255, blank=True, null=True, verbose_name=u'备注')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s:%s:%s' % (self.asset_id, self.slot, self.capacity)

    class Meta:
        verbose_name = 'RAM'
        verbose_name_plural = "RAM"
        unique_together = ("asset", "slot")

    auto_create_fields = ['sn', 'slot', 'model', 'capacity']


class Disk(models.Model):
    disk_iface_choice = (
        ('SATA', 'SATA'),
        ('SAS', 'SAS'),
        ('SCSI', 'SCSI'),
        ('SSD', 'SSD'),
    )
    asset = models.ForeignKey('Asset', db_column='asset')
    sn = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'SN号')
    slot = models.SmallIntegerField(u'插槽位')
    manufactory = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'制造商')
    model = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'磁盘型号')
    capacity = models.SmallIntegerField(u'磁盘容量GB')
    iface_type = models.CharField(max_length=16, choices=disk_iface_choice, default='SAS', verbose_name=u'接口类型')
    memo = models.CharField(max_length=255, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    auto_create_fields = ['sn', 'slot', 'manufactory', 'model', 'capacity', 'iface_type']

    class Meta:
        unique_together = ("asset", "slot")
        verbose_name = '硬盘'
        verbose_name_plural = "硬盘"

    def __unicode__(self):
        return '%s:slot:%s capacity:%s' % (self.asset_id, self.slot, self.capacity)


class NIC(models.Model):
    asset = models.ForeignKey('Asset', db_column='asset')
    name = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'网卡名')
    sn = models.CharField(max_length=64, blank=True, null=True)
    model = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'网卡型号')
    macaddress = models.CharField(max_length=32, unique=True, verbose_name=u'MAC')
    ipaddress = models.GenericIPAddressField(max_length=32, blank=True, null=True, verbose_name=u'IP')
    netmask = models.CharField(max_length=32, blank=True, null=True)
    bonding = models.CharField(max_length=8, blank=True, null=True)
    memo = models.CharField(max_length=255, blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s:%s' % (self.asset_id, self.macaddress)

    class Meta:
        verbose_name = u'网卡'
        verbose_name_plural = u"网卡"
        # unique_together = ("asset_id", "slot")

    auto_create_fields = ['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask', 'bonding']


class RaidAdaptor(models.Model):
    asset = models.ForeignKey('Asset', db_column='asset')
    sn = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'SN号')
    slot = models.CharField(max_length=64, verbose_name=u'插口数')
    model = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'型号')
    memo = models.CharField(max_length=255, blank=True, null=True)
    ctime = models.DateTimeField(auto_now_add=True)
    utime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ("asset", "slot")


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
    asset = models.ForeignKey('Asset', db_column='asset')
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
