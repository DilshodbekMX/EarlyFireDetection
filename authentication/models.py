from django.db import models
from django.contrib.auth.models import User
import os
from location_field.models.plain import PlainLocationField
from django.urls import reverse


class Profile(models.Model):
    # creating a relationship with user class (not inheriting)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    company = models.CharField(max_length=200, unique=True)
    city = models.CharField(max_length=30)
    location = PlainLocationField(based_fields=['city'], zoom=7)

    # adding additional attributes
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True)

    def __str__(self):
        return f'Profile for user {self.user.username}'
