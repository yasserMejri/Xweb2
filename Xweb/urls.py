"""Xweb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from fields import views

urlpatterns = [
	url(r'^$', views.index, name="index"), 
	url(r'^login/$', views.x_login, name="login"), 
    url(r'^logout/$', views.x_logout, name='logout'), 
	url(r'^register/$', views.x_register, name="register"), 
    url(r'^thankyou/$', views.x_thankyou, name="thankyou"), 
    url(r'^profile/$', views.x_profile, name="profile"), 
    url(r'^planselect/$', views.x_planselect, name="planselect"), 
	url(r'^database/$', views.database, name="database"), 
    url(r'^database/run/(?P<d_id>[0-9]+)/$', views.database_run, name="database-run"),
    url(r'^database/execute/(?P<d_id>[0-9]+)/$', views.database_execute, name="database-execute"),
    url(r'^database/download/(?P<d_id>[0-9]+)/$', views.download_result_csv, name="database-download-result"),
	url(r'^database/(?P<id>[0-9]+)/$', views.dbfields, name="database-detail"),
    url(r'^database/manage/$', views.dbfieldmanage, name="database-manage"), 
    url(r'^data-api/(?P<d_id>[0-9]+)/$', views.data_api, name="data-api"), 
    url(r'^api/$', views.api, name="database-api"), 

    url(r'^admin/', admin.site.urls, name = "admin"),

    url(r'^download/out/$', views.download_out, name="download_out"), 
    url(r'^download/crx/$', views.download_crx, name="download_crx"), 
]
