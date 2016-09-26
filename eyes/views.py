from django.shortcuts import render, HttpResponse


# Create your views here.


def index(request):
    xindex = 'hello world'
    return render(request, 'index.html', {'xindex': xindex})


def login(request):
    return HttpResponse('login')


def logout(request):
    return HttpResponse('logout')


def category(request):
    return HttpResponse('category')
