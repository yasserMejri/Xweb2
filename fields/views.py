# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import forms
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from wsgiref.util import FileWrapper
from django.utils.encoding import smart_str
from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from fields import models

from os.path import basename

import json
import csv
import os
import mimetypes
import string
import types
import zipfile

# Create your views here.

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
    	print files
        for file in files:
            ziph.write(os.path.join(root, file), basename(os.path.join(root, file)))

def index(request):
	return render(request, 'index.html')

def x_login(request):

	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')

		print username
		print password

		user = authenticate(request, username=username, password=password)

		print user

		if user is not None:
			login(request, user)
			return HttpResponseRedirect(reverse('database'))

	return render(request, 'login.html', {
		'form': forms.LoginForm
		})

def x_logout(request):
	logout(request)
	return HttpResponseRedirect(reverse('login'))

def x_register(request):

	print request.method

	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		email = request.POST.get('email')

		user = User(username=username, email=email)
		user.set_password(password)
		user.save()

		login(request, user)

		# SEND EMAIL WITH GENERATED email_code
		# Migrated to model side. plus integrated with User save signal
		# ---- SEND EMAIL ----

		return HttpResponseRedirect(reverse('thankyou'))

	return render(request, 'register.html', {
		'form': forms.RegisterForm
		})

@login_required
def x_thankyou(request):

	code = request.GET.get('code')
	action = 'register'
	user = request.user
	profile = models.Profile.objects.get(user=user)

	message = reverse('thankyou') + '?code='+profile.email_code

	if request.GET.get('sendagain'):
		profile.send_confirm_email()

	if code == profile.email_code:
		action = 'success'
		user.profile.email_code = ''
		user.profile.save()
		return HttpResponseRedirect(reverse('profile'))

	return render(request, 'thankyou.html', {
		'action': action, 
		'sendagain': reverse('thankyou') + '?sendagain=true'
		})

@login_required
def x_profile(request):

	profile = models.Profile.objects.get(user=request.user)

	if profile.email_code != '':
		return HttpResponseRedirect(reverse('thankyou'))

	plans = models.UserPlan.objects.all().order_by('fee')
	user = request.user
	form = forms.ProfileForm(initial={
		'username': user.username, 
		'email': user.email, 
		'first_name': user.first_name, 
		'last_name': user.last_name
		})

	password_form = forms.PasswordResetForm()

	error = ''
	msg = ''
	msg_type = ''

	if request.method == 'POST':

		if request.POST.get('resetpassword'):
			old_pw = request.POST.get('old_password')
			new_pw = request.POST.get('password')
			user = authenticate(request, username=user.username, password=old_pw)
			if user is None:
				error = 'Password Incorrect'
				msg = 'Password Incorrect'
				msg_type = 'danger'
			else:
				user.set_password(new_pw)
				user.save()
				msg_type = 'success'
				msg = 'Password Changed.'
		else:
			username = request.POST.get('username')
			email = request.POST.get('email')
			firstname = request.POST.get('first_name')
			lastname = request.POST.get('last_name')

			user.username = username
			user.email = email
			user.first_name = firstname
			user.last_name = lastname
			user.save()
			msg_type = 'success'
			msg = 'Saved Successfully'
		login(request, user)

	return render(request, 'profile.html', {
		'msg': msg, 
		'msg_type': msg_type, 
		'user': request.user, 
		'form': form, 
		'plans': plans, 
		'current_plan': profile.plan, 
		'password_form': password_form, 
		'error': error
		})

@login_required
def x_planselect(request):
	if request.method == 'GET':
		return HttpResponse('Bad Request')
	try:
		plan_id = request.POST.get('id')
		plan = models.UserPlan.objects.get(pk=plan_id)
		user = request.user
		profile = models.Profile.objects.get(user=user)
		profile.plan = plan
		profile.save()
		return HttpResponse(json.dumps({
			'status': 'success'
			}))
	except:
		return HttpResponse(json.dumps({
			'status': 'error', 
			'msg': 'Something Went Wrong!', 
			'request': request.POST
			}))

def refresh_db(d_id):
	database = models.UrlGroup.objects.get(pk=d_id)
	d_fields = models.XField.objects.filter(site_group = database)
	d_urls = models.Url.objects.filter(group = database)
	fields = {}
	urls = {}
	data = {}
	for item in d_fields:
		fields[item.id] = {
			'name': item.name,
			'rule': item.rule
		}
	for item in d_urls:
		urls[item.id] = {
			'url': item.url,
			'data': item.data, 
			'complete': item.complete,
		}
	return fields, urls, database

def pre_process(request):

	profile = models.Profile.objects.get(user=request.user)

	error = None

	if profile.email_code != '':
		error = HttpResponseRedirect(reverse('thankyou'))

	current_plan = profile.plan

	if current_plan == None:
		error = HttpResponseRedirect(reverse('profile'))

	return profile, current_plan, error

@login_required
def database(request):

	profile, current_plan, error = pre_process(request)

	if error:
		return error

	msg = ''
	msg_type= 'success'

	if request.method == 'POST':

		if request.POST.get('action') == 'run':
			database = models.UrlGroup.objects.get(pk=int(request.POST.get('id')))
			print reverse('database-run', kwargs={'d_id':database.id} )
			return HttpResponse(str(reverse('database-run', kwargs={'d_id':database.id} )))

		if request.POST.get('action') == 'delete-db':
			try:
				database = models.UrlGroup.objects.get(pk=int(request.POST.get('id')))
				fields = models.XField.objects.filter(site_group=database)
				urls = models.Url.objects.filter(group=database)
				for field in fields:
					field.delete()
				for url in urls:
					url.delete()
				database.delete()
				return HttpResponse(json.dumps({
					'status': 'success'
					}))
			except:
				return HttpResponse(json.dumps({
					'status': 'error'
					}))

		if request.POST.get('action') == 'create-db':

			db_count = len(models.UrlGroup.objects.filter(user=request.user))
			if current_plan.db_count != 0 and db_count >= current_plan.db_count:
				msg = 'You have reached maximum count of databases of your plan. You can upgrade your profile from <a href="'+reverse('profile')+'"> profile page </a>'
				msg_type = 'warning'
			else:
				db_name = request.POST.get('dbname')
				try:
					if len(models.UrlGroup.objects.filter(name=db_name, user=request.user)) != 0:
						raise ValueError('Same name exists!')
					db = models.UrlGroup(
						name = db_name, 
						user = request.user
						)
					db.save()
				except:
					msg = "A database with Same Name already exists! Please try with different name!"
					msg_type = 'error'

	all_dbs = models.UrlGroup.objects.filter(user=request.user)


	return render(request, 'database.html', {
		'user': request.user, 
		'all_dbs': all_dbs, 
		'msg': msg, 
		'msg_type': msg_type
		})

def create_execute_env(request, d_id):

	database = models.UrlGroup.objects.get(pk=d_id)

	os.system('mkdir ' + settings.SCRIPT_DIR)
	os.system('mkdir ' + settings.SCRIPT_DIR + str(request.user.id))
	os.system('mkdir ' + settings.SCRIPT_DIR + str(request.user.id) + '/' + database.name.replace(' ','_'))


	urls = models.Url.objects.filter(group = database, complete = True)
	fields = models.XField.objects.filter(site_group = database)

	original_script = ""
	with open(settings.SCRIPT_DIR + 'script.py') as f:
		original_script = f.read()

	script_content = original_script

	p_fields = {}
	for field in fields:
		p_fields[str(field.id)] = field.name

	print p_fields

	p_data = p_data_sq = None


	for url in urls:

		original_script = script_content

		p_data = json.loads(url.data)
		p_data_sq = json.loads(url.data_sq)
		p_data_urls = json.loads(url.data_urls)

		os.system('mkdir '+ settings.SCRIPT_DIR + str(request.user.id) + '/' + database.name.replace(' ','_') + '/' + url.url.replace('/','_'))

		target_dir = settings.SCRIPT_DIR + str(request.user.id) + '/' + database.name.replace(' ','_') + '/' + url.url.replace('/','_')

		original_script = original_script.replace('##FIELD_VALUE##', json.dumps(p_fields))
		original_script = original_script.replace("##DATA_VALUE##", json.dumps(p_data))
		original_script = original_script.replace("##DATA_SQ_VALUE##", json.dumps(p_data_sq))
		original_script = original_script.replace("##DATA_URLS_VALUE##", json.dumps(p_data_urls))
		original_script = original_script.replace("##TARGET_DIR_VALUE##", target_dir)
		original_script = original_script.replace('##SCRIPT_DIR##', settings.SCRIPT_DIR)

		print original_script

		with open(target_dir + '/script.py', 'w') as f:
			f.write(original_script)

		os.system('cd ' + target_dir)
		os.system('python ' + target_dir +'/script.py')


@login_required
def database_execute(request, d_id):

	if request.method == 'GET':
		return HttpResponse('Execute Database')

	profile, current_plan, error = pre_process(request)
	database = models.UrlGroup.objects.get(pk=d_id)

	if request.POST.get('show-data'):
		return data_api(request, d_id)

	create_execute_env(request, d_id)

	# if request.POST.get('now'):

	return HttpResponse(json.dumps({
		'status': 'success'
		}))

@csrf_exempt
def data_api(request, d_id):
	database = models.UrlGroup.objects.get(pk=d_id)
	urls = models.Url.objects.filter(group = database, complete = True)
	data = {}
	target_dir = settings.SCRIPT_DIR + str(request.user.id) + '/' + database.name.replace(' ','_') + '/'
	for url in urls:
		with open(target_dir + url.url.replace('/','_') + '/result.json') as f:
			data[url.url] = json.load(f)
	return HttpResponse(json.dumps(data))


@login_required
def download_result_csv(request, d_id):

	# if request.method == 'GET':
	# 	return HttpResponse('Post only')

	zip_dir = settings.TEMP_ZIP_DIR

	profile, current_plan, error = pre_process(request)
	database = models.UrlGroup.objects.get(pk=d_id)
	urls = models.Url.objects.filter(group = database, complete = True)

	target_dir = settings.TEMP_ZIP_DIR
	os.system('rm -rf ' + target_dir)
	os.system('mkdir ' + target_dir)
	for url in urls:
		source = settings.SCRIPT_DIR + str(request.user.id) + '/' + database.name.replace(' ','_') + '/' + url.url.replace('/','_')
		os.system('cp ' + source + '/result.csv ' + target_dir)
		os.system('mv ' + target_dir + 'result.csv ' + target_dir + url.url.replace('/','_') + '-result.csv')

	zip_path= settings.PROJECT_ROOT + '/out.zip'
	zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
	zipdir(target_dir, zipf)
	zipf.close()

	path = smart_str(zip_path)

	wrapper = FileWrapper( open( path, "r" ) )
	content_type = mimetypes.guess_type( path )[0]

	response = HttpResponse(wrapper, content_type = content_type)
	response['Content-Length'] = os.path.getsize( path ) # not FileField instance
	response['Content-Disposition'] = 'attachment; filename=%s' % smart_str( os.path.basename( path ) ) # same here

	return response	


@login_required
def database_run(request, d_id):

	profile, current_plan, error = pre_process(request)
	database = models.UrlGroup.objects.get(pk=d_id)

	if request.method == 'POST':
		interval = request.POST.get('data')
		database.interval = interval
		database.save()

		return HttpResponse(json.dumps({
			'status': 'success'
			}))

	try:
		interval = json.loads(database.interval)
	except:
		interval = database.interval

	weekdays = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
	repeat = ['once', 'everyday', 'custom']
	mode = ['append', 'overwrite']

	api_url = settings.SITE_URL + reverse('data-api', kwargs={'d_id': database.id})

	if error:
		return error

	return render(request, 'database-run.html', {
		'name': database.name,
		'database': database, 
		'user': request.user, 
		'weekdays': weekdays, 
		'api_url': api_url, 
		'interval': SafeString(json.dumps(interval)), 
		'repeat': repeat, 
		'mode': mode
		})

@login_required
def dbfields(request, id):

	profile, current_plan, error = pre_process(request)

	if error:
		return error

	msg_type = 'success'
	msg = ''

	try:
		database = models.UrlGroup.objects.get(pk=id)
	except:
		return HttpResponse("Bad Request")

	if database.user != request.user:
		return HttpResponse("404")

	if request.method == 'POST':
		if request.POST.get('action') == 'import-field':
			file = request.FILES['import-file']
			reader = csv.reader(file)
			database = models.UrlGroup.objects.get(pk=int(request.POST.get('d_id')))
			count = 0
			print "import-field"
			print reader
			rule_id = models.RuleType.objects.all()[0]
			for row in reader:
				print row
				try:
					new_field = models.XField(
						name = row[0], 
						rule = ','.join(row[1:]), 
						rule_id = rule_id,
						site_group = database
						)
					new_field.save()
					count = count + 1
				except:
					continue
			msg = "Success! " + str(count) + "field(s) have been added"
			msg_type = 'success'

		if request.POST.get('action') == 'import-url':
			file = request.FILES['import-file']
			reader = csv.reader(file)
			database = models.UrlGroup.objects.get(pk=int(request.POST.get('d_id')))
			count = 0
			for row in reader:
				try:
					new_url = models.Url(
						url = row[0], 
						group = database
						)
					new_url.save()
					count = count + 1
				except:
					continue
			msg = "Success! " + str(count) + "url(s) have been added"
			msg_type = 'success'

		if request.POST.get('action') == 'export':
			data = []
			header_fields = []
			if request.POST.get('type') == 'field':
				fields = models.XField.objects.filter(site_group = database)
				header_fields = ['name', 'rule']
				for field in fields:
					data.append([ field.name,  field.rule ])
			if request.POST.get('type') == 'url':
				urls = models.Url.objects.filter(group = database)
				header_fields = ['url']
				for url_ in urls:
					data.append([ url_.url ])
			if request.POST.get('type') == 'data':
				fields = models.XField.objects.filter(site_group = database)
				urls = models.Url.objects.filter(group = database)
				i = 0
				header_fields = ['Url']
				for field in fields:
					header_fields.append(field)
				for url_ in urls:
					try:
						raw_data = json.loads(url_.data.replace('|', '"'))
					except:
						raw_data = []
					print raw_data
					data.append([])
					data[i].append(url_.url)
					for field in fields:
						try:
							data[i].append(raw_data[str(field.id)])
						except:
							data[i].append("")
					i = i + 1

			print data

			path = smart_str(settings.PROJECT_ROOT+'/out.csv')
			with open(path, 'w') as f:
				writer = csv.writer(f)
				writer.writerow(header_fields)
				for row in data:
					print row
					writer.writerow([unicode(s).encode("utf-8") for s in row])
				f.close()

			return HttpResponse(json.dumps({
				'status': 'success'
				}))

		if request.POST.get('action') == 'refresh-table':
			try:
				fields, urls, database = refresh_db(int(request.POST.get('d_id')))
				print json.dumps(fields)
				print json.dumps(urls)
				return HttpResponse(json.dumps({
					'status': 'success', 
					'fields': fields, 
					'urls': urls
					}))
			except:
				return HttpResponse(json.dumps({
					'status': 'error',
					'msg': 'in refresh-table',
					'request': request.POST
					}))
		if request.POST.get('action') == 'update-table':
			try:
				data = json.loads(request.POST.get('data'))
				print data
				for key in data:
					url_ = models.Url.objects.get(pk=int(key))
					url_.data = data[key].replace('|', '"')
					url_.save()
				return HttpResponse(json.dumps({
					'status': 'success'
					}))
			except:
				return HttpResponse(json.dumps({
					'status': 'error', 
					'request': request.POST
					}))
		# return HttpResponse(json.dumps({
		# 		'status': msg_type, 
		# 		'msg': msg
		# 	}))


	name = database.name
	fields = models.XField.objects.filter(site_group = database)
	urls = models.Url.objects.filter(group = database)

	field_enable = True
	url_enable = True

	if len(fields) >= current_plan.field_count:
		field_enable = False

	if len(urls) >= current_plan.url_count:
		url_enable = False

	rules = models.RuleType.objects.all()

	return render(request, 'dbfields.html', {
		'user': request.user, 
		'name': name, 
		'rules': rules, 
		'd_id': database.id, 
		'fields': fields, 
		'urls': urls, 
		'msg': msg, 
		'msg_type': msg_type, 
		'field_enable': field_enable, 
		'url_enable': url_enable
		})

@login_required
def dbdatamanage(request):

	profile, current_plan, error = pre_process(request)

	if error:
		return error

	if request.method == 'Get':
		return HttpResponse('POST required')

	database = models.UrlGroup.objects.get(pk=int(request.POST.get('d_id')))

	if request.POST.get('action') == 'get-url-data':
		try:
			url_ = models.Url.objects.get(pk=int(request.POST.get('id')))
			return HttpResponse(json.dumps({
				'status': 'success', 
				'data': url_.data
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error'
				}))
	if request.POST.get('action') == 'set-url-data':
		try:
			url_ = models.Url.objects.get(pk=int(request.POST.get('id')))
			url_.data = request.POST.get('data')
			url_.save()
			return HttpResponse(json.dumps({
				'status': 'success', 
				'data': url_.data
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error', 
				}))

@login_required
def dbfieldmanage(request):

	profile, current_plan, error = pre_process(request)

	if error:
		return error

	if request.method == 'GET':
		return HttpResponse('POST required')

	database = models.UrlGroup.objects.get(pk=int(request.POST.get('d_id')))

	if request.POST.get('action') == 'new-field':
		field_count = len(models.XField.objects.filter(site_group=database))
		if field_count >= current_plan.field_count:
			return HttpResponse(json.dumps({
				'status': 'error', 
				'msg': 'count_exceed'
				}))
		print request.POST
		try:
			field = models.XField(
				name = request.POST.get('name'), 
				rule = request.POST.get('rule'), 
				rule_id = models.RuleType.objects.get(pk=int(request.POST.get('rule_id'))), 
				site_group = database
				)
			field.save()
			more = True
			if field_count + 1 == current_plan.field_count:
				more = False
			return HttpResponse(json.dumps({
				'status': 'success', 
				'id': field.id, 
				'more': more
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error'
				}))
	if request.POST.get('action') == 'update-field':
		try:
			field = models.XField.objects.get(pk=int(request.POST.get('id')))
			field.name =request.POST.get('name')
			field.rule_id = models.RuleType.objects.get(pk=int(request.POST.get('rule_type')))
			field.rule = request.POST.get('rule')
			field.save()
			return HttpResponse(json.dumps({
				'status': 'success'
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error'
				}))

	if request.POST.get('action') == 'new-url':
		url_count = len(models.Url.objects.filter(group=database))
		if url_count >= current_plan.url_count:
			return HttpResponse(json.dumps({
				'status': 'error', 
				'msg': 'count_exceed'
				}))
		try:
			url = models.Url(
				url =request.POST.get('url'), 
				group = database
				)
			url.save()
			more = True
			if url_count + 1 == current_plan.url_count:
				more = False
			return HttpResponse(json.dumps({
				'status': 'success',
				'id': url.id, 
				'more': more
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error'
				}))
	if request.POST.get('action') == 'update-url':
		try:
			url = models.Url.objects.get(pk=int(request.POST.get('id')))
			url.url = request.POST.get('url')
			url.save()
			return HttpResponse(json.dumps({
				'status': 'success'
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error'
				}))

	if request.POST.get('action') == 'del-field':
		try:
			field = models.XField.objects.get(pk=int(request.POST.get('id'))).delete()
			return HttpResponse(json.dumps({
				'status': 'success'
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error'
				}))

	if request.POST.get('action') == 'del-url':
		try:
			url = models.Url.objects.get(pk=int(request.POST.get('id'))).delete()
			return HttpResponse(json.dumps({
				'status': 'success'
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error'
				}))

@login_required
def download_out(request):

	path = smart_str(settings.PROJECT_ROOT+'/out.csv')

	wrapper = FileWrapper( open( path, "r" ) )
	content_type = mimetypes.guess_type( path )[0]

	response = HttpResponse(wrapper, content_type = content_type)
	response['Content-Length'] = os.path.getsize( path ) # not FileField instance
	response['Content-Disposition'] = 'attachment; filename=%s' % smart_str( os.path.basename( path ) ) # same here

	return response	

def download_crx(request):
	path = smart_str(settings.PROJECT_ROOT+'/extension.crx')
	wrapper = FileWrapper( open( path, "r" ) )
	content_type = mimetypes.guess_type( path )[0]

	response = HttpResponse(wrapper, content_type = content_type)
	response['Content-Length'] = os.path.getsize( path ) # not FileField instance
	response['Content-Disposition'] = 'attachment; filename=%s' % smart_str( os.path.basename( path ) ) # same here

	return response	

@csrf_exempt
def api(request):

	if request.method == 'GET':
		return HttpResponse("POST requests only")

	if request.POST.get('type') == 'login':
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = authenticate(request, username=username, password=password)
		if user is not None and user.profile.email_code == '':
			dbs = models.UrlGroup.objects.filter(user=user)
			databases = [{"id":item.id, "name":item.name} for item in dbs]
			return HttpResponse(json.dumps({
				'status': 'success', 
				'databases': databases, 
				'user': user.id
				}))
		else:
			return HttpResponse(json.dumps({
				'status': 'error', 
				'msg': 'Username or password is incorrect'
				}))

	if request.POST.get('type') == 'get_this': 
		try:
			user = User.objects.get(pk=int(request.POST.get('user')))
			fields, urls, database = refresh_db(int(request.POST.get('database')))
			dm = request.POST.get('home_url').split('/')[2]
			ud = models.Url.objects.filter(url__contains = dm, group = database)
			data = [{"id":item.id, "url": item.url, "data": item.data, "data_results": item.data_results, "data_sq": item.data_sq, "complete": item.complete} for item in ud]

			if len(data) == 0:
				return HttpResponse(json.dumps({
					'status': 'success', 
					'data': data,
					}))

			if len(data[0]['data']) == 0:
				data[0]['data'] = "{}";
			if len(data[0]['data_results']) == 0:
				data[0]['data_results'] = "{}"
			if len(data[0]['data_sq']) == 0:
				data[0]['data_sq'] = "{}"

			nxt_complete_url = ''
			nxt_url = ''
			flag = False
			for key in urls:
				if flag:
					if urls[key]['complete'] == False:
						nxt_complete_url = urls[key]['url']
						if nxt_url != '':
							break
					if nxt_url == '':
						nxt_url = urls[key]['url']
				if key == data[0]['id']:
					flag = True

			return HttpResponse(json.dumps({
				'status': 'success', 
				'fields': fields, 
				'urls': urls, 
				'data': data , 
				'nxt_url': nxt_url, 
				'nxt_complete_url': nxt_complete_url
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error',
				'msg': 'Something went wrong!', 
				'msg_type': '0', 
				'request': request.POST
				}))

	if request.POST.get('type') == 'save': 
		try:
			user = User.objects.get(pk=int(request.POST.get('user')))
			fields, urls, database = refresh_db(int(request.POST.get('database')))
			target = models.Url.objects.get(pk=int(request.POST.get('url_id')))

			data = json.loads(target.data) if len(target.data) != 0 else {}
			data_urls = json.loads(target.data_urls) if len(target.data_urls) != 0 else {}
			data_results = json.loads(target.data_results) if len(target.data_results) != 0 else {}
			data_sq = json.loads(target.data_sq) if len(target.data_sq) != 0 else []

			field = request.POST.get('field')
			if fields[int(field)]['name'] == 'next_url':

				try:
					if not isinstance(data[field], types.ListType):
						data[field] = []
				except:
					data[field] = []
				try:
					if not isinstance(data_urls[field], types.ListType):
						data_urls[field]
				except:
					data_urls[field] = []
				try:
					if not isinstance(data_results[field], types.ListType):
						data_results[field] = []
				except: 
					data_results[field] = []

				data[field].append(request.POST.get('content'))
				data_urls[field].append(request.POST.get('home_url'))
				data_results[field].append(request.POST.get('result'))

				n = 0
				for item in data_sq:
					if item.find(field) != -1:
						n = n + 1
				field = field + ' - ' + str(n)
			else:
				data[field] = request.POST.get('content')
				data_urls[field] = request.POST.get('home_url')
				data_results[field] = request.POST.get('result')

			try:
				data_sq.remove(field)
			except:
				pass
			data_sq.append(field)

			target.data = json.dumps(data)
			target.data_urls = json.dumps(data_urls)
			target.data_results = json.dumps(data_results)
			target.data_sq = json.dumps(data_sq)

			target.save()
			return HttpResponse(json.dumps({
				'status': 'success', 
				}))

		except:
			return HttpResponse(json.dumps({
				'status': 'error',
				'msg': 'Something went wrong!', 
				'msg_type': '0', 
				'request': request.POST
				}))

	if request.POST.get('type') == 'completeinverse':
		try:
			target = models.Url.objects.get(pk=int(request.POST.get('id')))
			target.complete  = not target.complete
			target.save()
			return HttpResponse(json.dumps({
				'status': 'success',
				'complete': target.complete, 
				'request': request.POST
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error',
				'msg': 'Something went wrong!', 
				'msg_type': '0', 
				'request': request.POST
				}))
	if request.POST.get('type') == 'saveorder':
		try:
			target = models.Url.objects.get(pk=int(request.POST.get('id')))
			target.data_sq = request.POST.get('sq_data')
			target.save()
			return HttpResponse(json.dumps({
				'status': 'success', 
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error',
				'msg': 'Something went wrong!', 
				'msg_type': '0', 
				'request': request.POST
				}))
	if request.POST.get('type') == 'saveurl':
		try:
			fields, urls, database = refresh_db(int(request.POST.get('database')))
			new_url = models.Url(
				url = request.POST.get('home_url').split('/')[2], 
				group = database, 
				data = "{}", 
				data_urls = "{}", 
				data_results = "{}", 
				complete = False
				)
			new_url.save()
			return HttpResponse(json.dumps({
				'status': 'success'
				}))
		except:
			return HttpResponse(json.dumps({
				'status': 'error',
				'msg': 'Something went wrong!', 
				'msg_type': '0', 
				'request': request.POST
				}))


	return HttpResponse(json.dumps({
		'status': 'none', 
		'request': request.POST
		}))
