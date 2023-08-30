from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'director'
urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='index'),
    # Camera
    path('cameraList/', views.AdminCameraListView.as_view(), name='cameraList'),
    path('cameraDetail/<pk>', views.cameraDetailView, name='cameraDetail'),
    path('addCamera/', views.AdminAddCameraView, name='addCamera'),
    # Detection
    path('detectionList/', views.AdminDetectionListView.as_view(), name='detectionList'),
    path('detectionDetail/<str:det_id>/', views.detectionDetailView, name='detectionDetail'),
    # Settings
    path('profileUpdate/', views.AdminUpdateProfileView, name='profileUpdate'),
    path('profileSetting/', views.AdminProfileSettingView, name='profileSetting'),
]
