from django.contrib import admin

from .models import CameraModel


# Register your models here.
class CameraModelAdmin(admin.ModelAdmin):
    list_display = ['camera_name', 'city', 'location', 'web_address']


admin.site.register(CameraModel, CameraModelAdmin)


