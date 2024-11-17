"""
URL configuration for pullup project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import HttpResponse
from rest_framework.documentation import include_docs_urls

# Customize admin interface
admin.site.site_header = 'Pullup Administration'
admin.site.site_title = 'Pullup Admin Portal'
admin.site.index_title = 'Welcome to Pullup Admin Portal'

def index(request):
    return HttpResponse("Pullup API is running. Visit <a href='/api/'>API</a>, <a href='/docs/'>Documentation</a>, or <a href='/admin/'>Admin Portal</a>")

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('docs/', include_docs_urls(title='Pullup API')),
]
