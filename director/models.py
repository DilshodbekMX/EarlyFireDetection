import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from location_field.models.plain import PlainLocationField
import validators
from django.utils.translation import gettext_lazy as _


# Create your models here.
def validate_url(value):
    if not validators.url(value):
        raise ValidationError(_("%(value)s is not an even number"), params={"value": value}, )


class CameraModel(models.Model):
    camera_name = models.CharField(max_length=50, unique=True)
    city = models.CharField(max_length=20)
    location = PlainLocationField(based_fields=['city'], zoom=10)
    web_address = models.CharField(max_length=100, unique=False, validators=[validate_url])
    added_date = models.DateTimeField(auto_now_add=True)

    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(blank=True, null=True)

    def __str__(self):
        return self.camera_name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.web_address)
        super().save(*args, **kwargs)


class DetectionModel(models.Model):
    detected_time = models.DateTimeField()
    image_url = models.CharField(max_length=1000, validators=[validate_url])
    accuracy = models.IntegerField(max_length=1)
    camera_id = models.ForeignKey(CameraModel, on_delete=models.CASCADE)
    offline_user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(blank=True, null=True)

    def __str__(self):
        return self.camera_id.camera_name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.camera_id.camera_name + self.detected_time)
        super().save(*args, **kwargs)


