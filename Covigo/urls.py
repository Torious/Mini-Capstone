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
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from messaging.views import list_notifications, toggle_read_notification, read_notification

from Covigo.settings import PRODUCTION_MODE

urlpatterns = [
    path('', lambda request: redirect('dashboard:index'), name='index'),
    path('manager/', include('manager.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('status/', include('status.urls')),
    path('appointments/', include('appointments.urls')),
    path('messaging/', include('messaging.urls')),
    path('symptoms/', include('symptoms.urls')),
    path('notifications/', list_notifications, name='list_notifications'),
    path('read_notification/<int:message_group_id>/', read_notification,
         name='read_notification'),
    path('toggle_read_notification/<int:message_group_id>/', toggle_read_notification,
         name='toggle_read_notification'),

]

if not PRODUCTION_MODE:
    urlpatterns.append(path('admin/', admin.site.urls))
