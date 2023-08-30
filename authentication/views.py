from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import LoginForm, UserRegistrationForm
from django.conf import settings
from django.core.files.storage import FileSystemStorage

auth = settings.FIREBASE_AUTH
db = settings.FIRESTORE_DB
# Create your views here.
def loginView(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('director:index')
                else:
                    return render(request, 'authentication/login.html',
                                  {'error_message': 'Disabled account', 'form': form})
            else:
                return render(request, 'authentication/login.html', {'error_message': 'Invalid login', 'form': form})
    else:
        form = LoginForm()
    return render(request, 'authentication/login.html', {'form': form})


def registerView(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            password = form.cleaned_data["password"]
            online_user = auth.create_user(email=email, password=password)
            data = {"email": email, "username": username, "password": password, "user_id": online_user.uid}
            db.collection("Users").document(online_user.uid).set(data)
            new_user.first_name = online_user.uid
            new_user.set_password(password)
            new_user.save()

            return render(request, 'authentication/register_done.html', {'new_user': new_user})
    else:
        form = UserRegistrationForm()
    return render(request, 'authentication/register.html', {'form': form})


@login_required
def logoutView(request):
    logout(request)
    return HttpResponseRedirect(reverse('inspector:index'))
