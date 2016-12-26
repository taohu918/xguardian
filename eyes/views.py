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

from assets import models

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
    return render(request, 'index.html', )


def account_login(request):
    err_msg = ''
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect('/eyes/index/')
        else:
            err_msg = "Wrong username or password!"
    return render(request, 'login.html', {'err_msg': err_msg})


def account_logout(request):
    logout(request)
    return HttpResponseRedirect('/eyes/login/')


@login_required
def assets(request):
    model_obj = models.Server.objects.all()
    data = model_obj
    role = 'admin'
    return render(request, 'assets.html', {'data': data, 'role': role})


@login_required
def details(request, uid):
    obj = models.Server.objects.get(uid=uid)
    # o = obj.os_set.select_related()
    # oo = o[0]
    # for i in o:
    #     print i
    # o = obj.os_set.get_os_types_choice_display()
    # print(uid, obj, obj.eventlog_set.select_related())
    return render(request, 'details.html', {'asset': obj})


@login_required
def net_res(request):
    return render(request, 'net_res.html')


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
    obj = models.IDC.objects.all()
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

            excel_to_db(file_path)

            # 保存信息到数据库
            info = request.POST['info']
            obj_type = request.POST['type']
            info_dic = {'info': info, 'obj_type': obj_type, 'path': file_path}
            # print(info_dic)

            models.UploadObj.objects.create(**info_dic)
            return HttpResponseRedirect('/eyes/lotupload/')

        else:
            err_msg = '请选择文件'

    return render(request, 'upload.html', {'err_msg': err_msg})


@login_required
def excel_to_db(excel):
    import xlrd
    import MySQLdb
    data = xlrd.open_workbook(excel)
    table = data.sheets()[0]
    nrows = table.nrows
    for i in range(1, nrows):
        print(table.row_values(i))


def batch(request):
    return render(request, 'batch_processing.html')


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


@login_required
def modifylog(request):
    # uid = request.GET.get('uid')
    # if uid:
    #     obj = models.EventLog.objects.filter(asset_uid_id=uid).order_by('create_time').reverse()
    #     return render(request, 'modify.html', {'modify_obj': obj, 'asset_uid': uid})
    # else:
    obj = models.EventLog.objects.all().order_by('create_time').reverse()
    return render(request, 'modifylog.html', {'modifylog_obj': obj})
