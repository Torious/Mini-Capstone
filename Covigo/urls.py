"""Covigo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import manager.views

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include


from Covigo.settings import PRODUCTION_MODE

urlpatterns = [
    path('', lambda request: redirect('dashboard:index'), name='index'),
    path('management/', include('manager.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('status/', include('status.urls')),
    path('appointments/', include('appointments.urls')),
    path('messaging/', include('messaging.urls.messaging')),
    path('symptoms/', include('symptoms.urls')),
    path('notifications/', include('messaging.urls.notifications')),
    path('help/', manager.views.help_page, name='help'),
    path('about/', manager.views.about, name='about'),

]

if not PRODUCTION_MODE:
    urlpatterns.append(path('admin/', admin.site.urls))
