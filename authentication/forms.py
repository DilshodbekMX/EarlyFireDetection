from django import forms
from django.core.exceptions import ValidationError
from location_field.forms.plain import PlainLocationField

from .models import Profile
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)



class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        r = User.objects.filter(email=email)
        if r.count():
            raise ValidationError("Email already taken!")
        return email

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        r = User.objects.filter(username=username)
        if r.count():
            raise ValidationError("Username already taken!")
        return username

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if password and password2 and password != password2:
            raise ValidationError("The password does not match!")

        return password2


class UserDetailCompleteForm(forms.ModelForm):
    company = forms.CharField(max_length=200, required=True)
    phone = forms.CharField(max_length=20, required=True)
    city = forms.CharField(max_length=40, required=True)
    location = PlainLocationField(based_fields=['city'],
                                  initial='41.311081,69.240562', zoom=10, required=True)

    class Meta:
        model = Profile
        fields = ['company', 'phone', 'city', 'location']

    def __init__(self, *args, **kwargs):
        super(UserDetailCompleteForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
