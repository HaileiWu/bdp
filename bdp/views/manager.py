# encoding: utf-8

from datetime import datetime
from bson.objectid import ObjectId
from functools import wraps

from flask import Blueprint
from flask import render_template
from flask import abort
from flask import request
from flask import Response
from flask import flash
from flask import redirect
from flask import url_for
from flask import json
from flask import jsonify
from flask import current_app as app
from flask.ext.paginate import Pagination

from flask.ext import login as flask_login
from flask.ext.login import login_required, current_user


from bdp import mongo, login_manager

def to_int(num, default=0):
	""" 转化为整形 """
	try:
		return int(num)
	except Exception, e:
		return default

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(username):
	manager = mongo.db.managers.find_one({'username': username})

	if not manager:
		return

	user = User()
	user.id = username
	user.role = manager.get('role')
	return user

@login_manager.request_loader
def request_loader(request):
	username = request.form.get('username')
	manager = mongo.db.managers.find_one({'username': username})
	if not manager:
		return

	user = User()
	user.id = username
	user.role = manager.get('role')
	return user


page = Blueprint('manager', __name__, template_folder='templates')

@page.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')

	# 从数据库里获取用户信息
	username = request.form['username']
	manager = mongo.db.managers.find_one({'username': username})

	if manager and manager.get('enable') == False:
		flash('账户不可用')
		return render_template('login.html')

	# 验证密码是否正确
	if manager and request.form['password'] == manager.get('password'):
		user = User()
		user.id = username
		user.role = manager.get('role')

		flask_login.login_user(user)

		return redirect(url_for('user.index'))

	flash('用户名或密码错误！')
	return render_template('login.html')

@page.route('/logout')
def logout():
	flask_login.logout_user()
	return redirect(url_for('manager.login'))

@page.route('/managers')
@login_required
def index():
	limit = 100
	page = int(request.args.get('page', 1))
	if current_user.role == 'root':
		q = {}
	else:
		q = {'created_by': current_user.id}
	managers = mongo.db.managers.find(q)
	total = mongo.db.managers.count(q)
	pagination = Pagination(page=page, total=total, record_name='')
	return render_template('managers/index.html', managers=managers, pagination=pagination)

@page.route('/manager/new', methods=['GET'])
@login_required
def new():
	manager = {}
	if current_user.role == 'agent':
		current_mananger = mongo.db.managers.find_one({'username': current_user.id})
		hint = '已使用语音授权：%s/%s，已使用siri授权：%s/%s，已使用匿名授权：%s/%s' % \
		(current_mananger['used_voice_licenses'], current_mananger['voice_licenses'],
			current_mananger['used_siri_licenses'], current_mananger['siri_licenses'],
			current_mananger.get('used_anonymous_licenses', 0), current_mananger.get('anonymous_licenses',0),)
		manager['hint'] = hint

	return render_template('managers/new.html', manager=manager)

@page.route('/managers', methods=['POST'])
@login_required
def create():
	form = request.form
	username = form['username'].strip()
	password = form['password'].strip()
	backup = form['backup']
	enable = form['enable']
	role = form.get('role', 'sub-agent')
	voice_licenses = to_int(form['voice_licenses'])
	siri_licenses = to_int(form['siri_licenses'])
	anonymous_licenses = to_int(form['anonymous_licenses'])
	licenses = voice_licenses + siri_licenses + anonymous_licenses
	created_at = datetime.now()
	
	if current_user.role == 'agent':
		# 获取当前管理员数据
		manager = mongo.db.managers.find_one({'username': current_user.id})
		manager_voice_licenses = manager.get('voice_licenses')
		manager_siri_licenses = manager.get('siri_licenses')
		manager_anonymous_licenses = manager.get('anonymous_licenses')
		manager_used_voice_licenses = manager.get('used_voice_licenses')
		manager_used_siri_licenses = manager.get('used_siri_licenses')
		manager_used_anonymous_licenses = manager.get('used_anonymous_licenses')

		if voice_licenses + manager_used_voice_licenses > manager_voice_licenses:
			flash('语音授权超出可用值！')
			return redirect(url_for('manager.index'))
		if siri_licenses + manager_used_siri_licenses > manager_siri_licenses:
			flash('siri授权超出可用值！')
			return redirect(url_for('manager.index'))
		if anonymous_licenses + manager_used_anonymous_licenses > manager_anonymous_licenses:
			flash('匿名授权超出可用值！')
			return redirect(url_for('manager.index'))
		# 增量
		inc = {
			'used_licenses': voice_licenses + siri_licenses + anonymous_licenses, 
			'used_voice_licenses': voice_licenses, 
			'used_siri_licenses': siri_licenses,
			'used_anonymous_licenses': anonymous_licenses,
		}
		mongo.db.managers.update({'username': current_user.id}, {'$inc': inc})


	data = {
		'username': username,
		'password': password,
		'backup': backup,
		'licenses': licenses,
		'voice_licenses': voice_licenses,
		'siri_licenses': siri_licenses,
		'anonymous_licenses': anonymous_licenses,
		'enable': enable == 'true' and True or False,
		'used_licenses': 0,
		'used_voice_licenses': 0,
		'used_siri_licenses': 0,
		'used_anonymous_licenses': 0,
		'role': role,
		'created_at': created_at,
		'created_by': current_user.id,
	}

	manager_id = mongo.db.managers.insert_one(data).inserted_id

	return redirect(url_for('manager.index'))

@page.route('/manager/update/<manager_id>', methods=['POST'])
@login_required
def update(manager_id):
	form = request.form 
	username = form['username'].strip()
	password = form['password'].strip()
	backup = form['backup']
	enable = form['enable']
	role = form.get('role', 'sub-agent')
	voice_licenses = to_int(form['voice_licenses'])
	siri_licenses = to_int(form['siri_licenses'])
	anonymous_licenses = to_int(form['anonymous_licenses'])
	licenses = voice_licenses + siri_licenses + anonymous_licenses

	if current_user.role == 'agent':
		# 获取当前管理员数据
		manager = mongo.db.managers.find_one({'username': current_user.id})
		manager_voice_licenses = manager.get('voice_licenses')
		manager_siri_licenses = manager.get('siri_licenses')
		manager_anonymous_licenses = manager.get('anonymous_licenses')
		manager_used_voice_licenses = manager.get('used_voice_licenses')
		manager_used_siri_licenses = manager.get('used_siri_licenses')
		manager_used_anonymous_licenses = manager.get('used_anonymous_licenses')

		if voice_licenses + manager_used_voice_licenses > manager_voice_licenses:
			flash('语音授权超出可用值！')
			return redirect(url_for('manager.index'))
		if siri_licenses + manager_used_siri_licenses > manager_siri_licenses:
			flash('siri授权超出可用值！')
			return redirect(url_for('manager.index'))
		if anonymous_licenses + manager_used_anonymous_licenses > manager_anonymous_licenses:
			flash('匿名授权超出可用值！')
			return redirect(url_for('manager.index'))
		# 增量
		inc = {
			'used_licenses': voice_licenses + siri_licenses + anonymous_licenses, 
			'used_voice_licenses': voice_licenses, 
			'used_siri_licenses': siri_licenses,
			'used_anonymous_licenses': anonymous_licenses,
		}
		mongo.db.managers.update({'username': current_user.id}, {'$inc': inc})

	manager = {
		'username': username,
		'password': password,
		'backup': backup,
		'role': role,
		'anonymous_licenses': anonymous_licenses,
		'voice_licenses': voice_licenses,
		'siri_licenses': siri_licenses,
		'licenses': licenses,
		'enable': enable == 'true' and True or False,
	}

	result = mongo.db.managers.update_one({'_id': ObjectId(manager_id)}, {'$set': manager})

	return redirect(url_for('manager.index'))

@page.route('/manager/edit/<manager_id>', methods=['GET'])
@login_required
def edit(manager_id):
	manager = mongo.db.managers.find_one({'_id': ObjectId(manager_id)})
	return render_template('managers/edit.html', manager=manager)

@page.route('/manager/show/<manager_id>', methods=['GET'])
@login_required
def show(manager_id):
	manager = mongo.db.managers.find_one({'_id': ObjectId(manager_id)})
	users = mongo.db.users.find({'created_by': manager.get('username')})
	return render_template('managers/show.html', manager=manager, users=users)

@page.route('/manager/disable/<manager_id>', methods=['GET'])
def disable(manager_id):
	result = mongo.db.managers.update_one({'_id': ObjectId(manager_id)}, {'$set': {'enable': False}})
	return redirect(url_for('manager.index'))

@page.route('/manager/delete/<manager_id>', methods=['GET'])
def delete(manager_id):
	mongo.db.managers.remove({'_id': ObjectId(manager_id)})
	return redirect(url_for('manager.index'))

