from django.contrib import admin

from .models import Profile


# Register your models here.
class ProfileModelAdmin(admin.ModelAdmin):
    list_display = ['company', 'city', 'location', 'phone']


admin.site.register(Profile, ProfileModelAdmin)
