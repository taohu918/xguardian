# -*- coding: utf-8 -*-
# __author__: taohu

from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from userauth.forms import *
from django.contrib.auth import authenticate
from userauth.models import UserProfile
import json


# Create your views here.
@login_required
def changepwd(request):
    if request.method == 'GET':
        form = ChangepwdForm()
        print(form)
        return render(request, 'changepwd.html', {'form': form})
    else:
        form = ChangepwdForm(request.POST)
        if form.is_valid():
            name = request.user
            oldpassword = request.POST.get('oldpassword', '')
            user = authenticate(username=name, password=oldpassword)
            if user is not None and user.is_active:
                newpassword = request.POST.get('newpassword1', '')
                user.set_password(newpassword)
                user.save()
                return render(request, 'index.html')
            else:
                return render(request, 'changepwd.html', {'form': form, 'oldpassword_is_wrong': True})
        else:
            return render(request, 'changepwd.html', {'form': form})


def account_data(request):
    account_data_list = []
    obj = UserProfile.objects.all()
    total = 0
    for account in obj:
        if account.is_active == 1:
            status = 'valid'
        else:
            status = 'invalid'
        tmp_dic = {
            "is_active": status,
            "id": account.id,
            "name": account.name,
            "email": account.email,
        }
        account_data_list.append(tmp_dic)
        total += 1

    format_data = {
        "total": total,
        "rows": account_data_list
    }
    print(83, format_data)
    return HttpResponse(json.dumps(format_data), )


def row_data_save(request):
    is_active = request.POST.get('is_active')
    if is_active == 'valid':
        is_active = 1
    else:
        is_active = 0

    user_obj = UserProfile.objects.get(id=request.POST.get('id'))
    user_obj.email = request.POST.get('email')
    user_obj.name = request.POST.get('name')
    user_obj.is_active = is_active
    user_obj.save()
    # 更新多个字段或一个字段
    # user_obj.update(email=request.POST.get('email'), name=request.POST.get('name'))

    new_user_info = {
        'id': request.POST.get('id'),
        'email': request.POST.get('email'),
        'name': request.POST.get('name'),
        'is_active': is_active,
    }
    print(new_user_info)
    return HttpResponse(json.dumps(new_user_info))
