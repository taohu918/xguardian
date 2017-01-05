from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from userauth.forms import *
from django.contrib.auth import authenticate


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
