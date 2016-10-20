# -*- coding: utf-8 -*-
# __author__: taohu
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from assets import models


# Create your views here.


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


# TODO: 分页
class NumFactory(object):
    page_total = 20

    def __init__(self, page_id):
        self.page_id = int(page_id)
        self.page_show_num = NumFactory.page_total

    # 内容条目
    @property
    def start(self):
        return (self.page_id - 1) * self.page_show_num

    @property
    def end(self):
        return self.page_id * self.page_show_num

    def pagination(self, all_rows, url):
        quotient, remainder = divmod(all_rows, self.page_show_num)

        # 确定最后一页页码
        if remainder > 0:
            quotient += 1

        # 确定起始页、结束页页码
        if quotient <= 11:  # 总页数少于 11 时
            start = 1
            end = quotient
        else:  # 总页数大于 11 时
            if self.page_id < 6:
                start = 1
                end = 11
            else:
                start = self.page_id - 5
                end = self.page_id + 5
                if end > quotient:
                    end = quotient
                    start = quotient - 11

        paginate = ''
        for i in range(start, end + 1):  # end + 1, 否则分页码少一
            if i == self.page_id:
                temp = "<li class='active'><a href='%s%s'>%s<span class='sr-only'>(current)</span></a></li>" \
                       % (url, i, i)
            else:
                temp = "<li><a href='%s%s'>%s</a></li>" % (url, i, i)
            paginate += temp

        if self.page_id > 1:
            last_page = "<li><a href='%s%s'>&laquo;</a><li>" % (url, self.page_id - 1)
        else:
            last_page = "<li><a href='javascript:void(0)'>&laquo;</a></li>"

        if self.page_id >= quotient:
            next_page = "<li><a href='javascript:void(0)'>&raquo;</a></li>"
        else:
            next_page = "<li><a href='%s%s'>&raquo;</a></li>" % (url, self.page_id + 1)

        paginate = "<nav> <ul class='pagination'>" + last_page + paginate + next_page + "</ul> </nav>"
        return paginate


def assets(request):
    page_id = request.GET.get('pid', 1)
    model_obj = models.Server.objects.all()
    page_obj = NumFactory(page_id)
    data = model_obj[page_obj.start:page_obj.end]
    all_rows = model_obj.count()

    # data = range(200)[page_obj.start:page_obj.end]
    all_rows = 200
    paginations = page_obj.pagination(all_rows, '/eyes/assets/?pid=')
    return render(request, 'assets.html', {'data': data, 'pagination': paginations})


def details(request, uid):
    obj = models.Server.objects.get(uid=uid)
    # o = obj.os_set.select_related()
    # oo = o[0]
    # for i in o:
    #     print i
    # o = obj.os_set.get_os_types_choice_display()
    return render(request, 'details.html', {'asset': obj})


def modifylog(request):
    uid = request.GET.get('uid')
    if uid:
        obj = models.EventLog.objects.filter(asset_uid_id=uid).order_by('create_time').reverse()
        return render(request, 'modify.html', {'modify_obj': obj, 'asset_uid': uid})
    else:
        obj = models.EventLog.objects.all()
        return render(request, 'modifylog.html', {'modifylog_obj': obj})
