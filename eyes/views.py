# -*- coding: utf-8 -*-
# __author__: taohu

import json
import sys
import threading
from assets.utilsbox import api_paramiko
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page, cache_control

from assets import models
from userauth.models import UserProfile

if sys.version.split('.')[0] == '3':
    import queue

    q = queue.Queue(maxsize=1000)
    upload_q = queue.Queue(maxsize=1000)
elif sys.version.split('.')[0] == '2':
    import Queue

    q = Queue.Queue(maxsize=1000)
    upload_q = Queue.Queue(maxsize=1000)


# Create your views here.
@csrf_exempt
def post_test(request):
    return HttpResponse('this is a test func.')


@login_required
def index(request):
    return render(request, 'index.html')


def account_login(request):
    err_msg = False

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/eyes/index/')
            # return HttpResponseRedirect(request.session['login_from'])
        else:
            err_msg = True
    return render(request, 'login.html', {'err_msg': err_msg})


def account_logout(request):
    logout(request)
    return HttpResponseRedirect('/eyes/login/')


@login_required
# @cache_page(60 * 60 * 24)
def assets(request):
    data = models.Server.objects.filter(idc__type='IDC')
    # data.user_id = request.user.id
    return render(request, 'assetManage/assets.html', {'data': data})


# @cache_control(private=True, max_age=28800)
# @cache_page(60 * 60 * 24)
@login_required
def assets_new(request):
    print(request.user.email)
    data = models.Server.objects.all()
    return render(request, 'assetManage/assets_new.html', {'data': data})


@login_required
def assets_auth(request):
    asset_uid = request.POST.get('asset_uid')
    user_id = request.user.id

    role_list = []
    role_obj = UserProfile.objects.get(id=user_id).userrole_set.all()
    for role_item in role_obj:
        role_list.append(role_item.roleid.name)

    if 'admin' in role_list:
        secret = models.Server.objects.get(uid=asset_uid).password
        return HttpResponse(json.dumps(secret))
    else:
        return HttpResponse(json.dumps('Permission Denied'))


@login_required
def details(request, uid):
    obj = models.Server.objects.get(uid=uid)
    # o = obj.os_set.select_related()
    # oo = o[0]
    # for i in o:
    #     print i
    # o = obj.os_set.get_os_types_choice_display()
    # print(uid, obj, obj.eventlog_set.select_related())
    return render(request, 'assetManage/details.html', {'asset': obj})


@login_required
def assets_pro(request):
    pro_objs = models.IDC.objects.filter(type='PRO')
    for i in pro_objs:
        print(i.name, i.city, i.mark, i.type)
    return render(request, 'assetManage/projects.html', {'pro_objs': pro_objs})


@login_required()
def assets_pro_list(request, pro_mark):
    # 使用__来查询相关连的表里的数据
    print(pro_mark)
    obj = models.Server.objects.filter(idc__mark=pro_mark)
    return render(request, 'assetManage/assets.html', {'data': obj})


@login_required()
def assets_pro_detail(request, uid):
    obj = models.Server.objects.get(uid=uid)
    return render(request, 'assetManage/details.html', )


@login_required
def net_res(request):
    return render(request, 'assetManage/net_res.html')


@login_required
def get_idc_list(request):
    data = []
    # obj = models.IDC.objects.all().values('area')
    obj = models.IDC.objects.all()
    for item in obj:
        num = models.Server.objects.filter(idc_id=item.id).count()
        data.append({'name': item.name, 'value': num})
    # print(data)
    return HttpResponse(json.dumps(data))


@login_required
def get_idc_bw(request):
    data = []
    obj = models.IDC.objects.filter(type='IDC')
    for item in obj:
        data.append({'name': item.name, 'value': item.bandwidth.split('Mb')[0]})
    return HttpResponse(json.dumps(data))


@login_required
def lotupload(request):
    import os
    err_msg = ''
    if request.method == "POST":
        if request.FILES:
            file_data = request.FILES
            file_obj = file_data.get('file_name')
            # print(file_obj.name, file_obj.size)

            file_path = os.path.join('static/upload/', file_obj.name)
            f = open(file_path, 'wb')
            for line in file_obj.chunks():
                f.write(line)
            f.close()

            # 把Excel内容导入到资产库
            # excel_to_db(file_path)
            mth_obj = ExcelToDB(file_path)
            mth_obj.excel_to_db()

            # 保存上传的文件信息到数据库
            info = request.POST['info']
            obj_type = request.POST['type']
            info_dic = {'info': info, 'obj_type': obj_type, 'path': file_path}

            models.UploadObj.objects.create(**info_dic)
            return HttpResponseRedirect('/eyes/lotupload/')

        else:
            err_msg = '请选择文件'

    return render(request, 'assetManage/upload.html', {'err_msg': err_msg})


class ExcelToDB(object):
    def __init__(self, excel):
        self.excel = excel
        self.manufactory = None
        self.business = None
        self.idc = None

    def excel_to_db(self):
        import xlrd
        data = xlrd.open_workbook(self.excel)
        table = data.sheets()[0]
        nrows = table.nrows
        for i in range(2, nrows):
            info_list = table.row_values(i)
            if info_list[10]:
                expired_date = info_list[10]
            else:
                expired_date = '2016-01-01'

            data_dic = {
                'uid': info_list[0] + '_' + info_list[8],
                'sn': info_list[1],
                'name': info_list[2],
                'model': info_list[3],
                'ram_size': info_list[4],
                'ip': info_list[8],
                'hosted': info_list[9],
                'expired_date': expired_date,
                'loginname': info_list[12],
                'password': info_list[13],
                'position': info_list[14],
            }
            obj = models.Server(**data_dic)
            obj.save()

            self.manufactory = info_list[5]
            manufactory_obj = self.check_manufactory()
            obj.manufactory = manufactory_obj

            if info_list[6]:
                self.business = u'%s' % info_list[6]
            else:
                self.business = u'未知'
            business_obj = self.check_business()
            obj.business = business_obj

            # self.idc = info_list[7]
            # idc_obj = self.check_idc()
            # obj.idc = idc_obj

            obj.save()

    def check_manufactory(self):
        obj = models.Manufactory.objects.filter(manufactory=self.manufactory)
        if obj:
            this_obj = obj[0]
        else:
            this_obj = models.Manufactory(manufactory=self.manufactory)
            this_obj.save()
        return this_obj

    def check_business(self):
        obj = models.Business.objects.filter(name=self.business)
        if obj:
            this_obj = obj[0]
        else:
            this_obj = models.Business(name=self.business)
            this_obj.save()
        return this_obj

    def check_idc(self):
        obj = models.IDC.objects.filter(name=self.idc)
        if obj:
            this_obj = obj[0]
        else:
            this_obj = models.IDC(name=self.idc)
            this_obj.save()
        return this_obj


def batch(request):
    return render(request, 'serverManage/batch_processing.html')


def post_cmds(request):
    cmds_str = request.POST.get('cmds_str', False)
    ip_str = request.POST.get('ip_str', False)

    paramiko_obj = api_paramiko.APIParamiko()
    num = len(ip_str.split(','))
    for host in ip_str.split(','):
        t = threading.Thread(target=paramiko_obj.ssh_exec_cmd, args=(host, 'root', 22, cmds_str, q))
        t.start()
    return HttpResponse(json.dumps(num))


def get_cmds_res(request):
    try:
        cmds_res = q.get(timeout=5)
        ip = cmds_res.keys()[0]
        command_format = '\n%s:\nCommand: %s   StartTime: %s   Cost: %s \nResult: %s' % (
            cmds_res.keys()[0], cmds_res[ip][2], cmds_res[ip][0], cmds_res[ip][1], cmds_res[ip][3])
        return HttpResponse(json.dumps(command_format))
    except Exception as e:
        print(e)
        return HttpResponse('false')


def file_distribution(request):
    if request.method == 'POST':
        from assets.utilsbox import form_verify

        target_host = request.POST['target_host']
        target_path = request.POST['target_path']
        source_file = request.POST['source_file']
        num = len(target_host.split(','))

        uf = form_verify.UploadObj(request.POST, request.FILES)  # form验证字段应与表单中的name对应, 即表单传什么我就验证什么
        if uf.is_valid():
            # 获取表单信息 {key: value}
            upload_obj = uf.cleaned_data['upload_obj']  # 根据表单元素的 name 获取其 value
            # target_host = uf.cleaned_data['target_host']

            # 写入数据库
            upload = models.UploadObj()
            upload.path = upload_obj
            upload.save()

            for host in target_host.split(','):
                trans_obj = api_paramiko.APIParamiko()
                t = threading.Thread(
                    target=trans_obj.obj_upload,
                    args=(host, 'root', 22, source_file, target_path, upload_q)
                )
                t.start()
        return HttpResponse(json.dumps(num))
    else:
        return render(request, 'serverManage/file_distribution.html')


def get_distribution_res(request):
    try:
        distribution_res = upload_q.get(timeout=5)
        ip = distribution_res.keys()[0]
        result = '\n%s:\nFile: %s   StartTime: %s   Cost: %s \nResult: %s' % (
            ip, distribution_res[ip][2], distribution_res[ip][0], distribution_res[ip][1], distribution_res[ip][3])
        return HttpResponse(json.dumps(result))
    except Exception as e:
        print(e)
        return HttpResponse('false')


@login_required()
def account_manage(request):
    return render(request, 'accountManage/account_manage.html')


@login_required
def modifylog(request):
    # uid = request.GET.get('uid')
    # if uid:
    #     obj = models.EventLog.objects.filter(asset_uid_id=uid).order_by('create_time').reverse()
    #     return render(request, 'modify.html', {'modify_obj': obj, 'asset_uid': uid})
    # else:
    obj = models.EventLog.objects.all().order_by('create_time').reverse()
    return render(request, 'modifylog.html', {'modifylog_obj': obj})
