"""DSCHA_ClientAgent URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.conf.urls import url
from django.urls import path

from app.views import main_page, ClientView, ServerView, CreateTCPTraffic
from app import api as app_api

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^$', main_page, name='main'),
    url(r'^client/$', ClientView.as_view(), name='client'),
    url(r'^server/$', ServerView.as_view(), name='server'),
    url(r'^udptraffic/add/$', CreateTCPTraffic.as_view(), name='add-tcp-traffic'),

    # RestAPI urls
    url(r'^api/v1/UDPTraffics/$', app_api.UDPTrafficListCreateApiView.as_view()),
    url(r'^api/v1/UDPTraffics/(?P<pk>[0-9]+)/$', app_api.UDPTrafficDetailApiView.as_view()),
    url(r'^api/v1/UDPServers/$', app_api.UDPServerListCreateApiView.as_view()),
    url(r'^api/v1/UDPServers/(?P<pk>[0-9]+)/$', app_api.UDPServerDetailApiView.as_view())
]
