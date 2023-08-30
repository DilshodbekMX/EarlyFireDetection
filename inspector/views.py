from django.shortcuts import render
from django.views.decorators import gzip
from django.conf import settings
from django.core.files.storage import FileSystemStorage


# Create your views here.
@gzip.gzip_page
def index(request):
    return render(request=request, template_name="inspector/index.html")



