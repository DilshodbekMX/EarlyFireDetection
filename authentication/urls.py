from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'authentication'

urlpatterns = [
    path(r'login/', views.loginView, name='login'),
    path(r'register/', views.registerView, name='register'),
    path(r'logout/', views.logoutView, name='logout'),

]