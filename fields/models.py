# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

import jsonfield

# Create your models here.

class UserPlan(models.Model):
	title = models.CharField(max_length=50)
	db_count = models.IntegerField()
	field_count = models.IntegerField()
	url_count = models.IntegerField()
	fee = models.IntegerField()

	def __str__(self):
		return self.title

class Profile(models.Model):
	user = models.OneToOneField(User)
	plan = models.ForeignKey(UserPlan, null=True, default=None)
	email_code = models.CharField(max_length=255)

	def __str__(self):
		return self.user.username

class RuleType(models.Model):
	name = models.CharField(max_length=50)
	field_enable = models.BooleanField(default = True)
	placeholder = models.CharField(max_length=50)
	required = models.BooleanField(default=True)
	default = models.CharField(max_length=255, blank=True)

	def __str__(self):
		return self.name

class XField(models.Model):
	name = models.CharField(max_length=50)
	rule = models.CharField(max_length=255, blank=True, null=True) # JSON formatted string for storing all regex rules.
	rule_id = models.ForeignKey(RuleType)
	site_group = models.ForeignKey("UrlGroup")

	def __str__(self):
		return self.name

class UrlGroup(models.Model):
	name = models.CharField(max_length=255)
	user = models.ForeignKey(User)
	interval = jsonfield.JSONField()

	def __str__(self):
		return self.name

class Url(models.Model):
	url = models.CharField(max_length=255)
	group = models.ForeignKey(UrlGroup)
	data = models.TextField(blank=True)
	data_urls = models.TextField(blank=True)
	data_results = models.TextField(blank=True)
	data_sq = models.TextField(blank=True)
	complete = models.BooleanField(default=False)

	def __str__(self):
		return self.url
