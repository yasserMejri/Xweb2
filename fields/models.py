# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from crontab import CronTab

import jsonfield
import json

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

	def save(self, *args, **kwargs):
		super(UrlGroup, self).save(*args, **kwargs)	
		cron = CronTab(user = True)
		jobs = []
		urls = Url.objects.filter(group = self, complete = True)

		interval = json.loads(self.interval)
		cmt = 'Xpath database ' + str(self.id)

		for job in cron:
			if job.comment == cmt:
				cron.remove(job)
		cron.write()

		cron_string = ''
		if 'once' == interval['repeat']:
			cron_string = interval['data']['time'].split(':')[1] + ' ' + interval['data']['time'].split(':')[0] + ' '
			cron_string += interval['data']['date'].split('-')[0] + ' ' + interval['data']['date'].split('-')[1] + ' *'
		if 'everyday' == interval['repeat']:
			cron_string = interval['data']['time'].split(':')[1] + ' ' + interval['data']['time'].split(':')[0] + ' '
			cron_string += '* * *'
		if 'custom' == interval['repeat']:
			cron_string = []
			for dow in interval['data']:
				item = interval['data'][dow].split(':')[1] + ' ' + interval['data'][dow].split(':')[0] + ' * * '
				item += dow.upper()
				cron_string.append(item)

		for url in urls:
			target_dir = settings.SCRIPT_DIR + str(self.user.id) + '/' + self.name + '/' + url.url  + '/script.py'
			if isinstance(cron_string, basestring):
				job = cron.new(command='python ' + target_dir, comment=cmt)
				job.setall(cron_string)
				cron.write()
			else:
				for item in cron_string:
					job = cron.new(command='python ' + target_dir, comment=cmt)
					job.setall(item)
					cron.write()

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
