from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'inspector'

urlpatterns = [
    path(r'', views.index, name='index'),
]