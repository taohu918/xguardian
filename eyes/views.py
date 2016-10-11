from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout


# Create your views here.


def index(request):
    xindex = 'hello world'
    if request.user.is_authenticated:
        print request.user.name
    return render(request, 'index.html', {'xindex': xindex})


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


def assets(request):
    return render(request, 'assets.html')
