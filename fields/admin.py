# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from fields import models

# Register your models here.

class Url(admin.TabularInline):
	model = models.Url

class XField(admin.TabularInline):
	model = models.XField

class UrlGroupAdmin(admin.ModelAdmin):
	inlines = [
		XField, 
		Url
	]

class UserCreationFormExtended(UserCreationForm): 
    def __init__(self, *args, **kwargs): 
        super(UserCreationFormExtended, self).__init__(*args, **kwargs) 
        self.fields['email'] = forms.EmailField(label=_("E-mail"), max_length=75)

UserAdmin.add_form = UserCreationFormExtended
UserAdmin.add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('email', 'username', 'password1', 'password2',)
    }),
)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(models.UrlGroup, UrlGroupAdmin)

admin.site.register(models.RuleType)

admin.site.register(models.UserPlan)
