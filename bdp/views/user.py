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
from flask_paginate import Pagination

from flask.ext.login import current_user
from flask.ext.login import login_required

from pymongo.errors import DuplicateKeyError

from bdp import mongo

def to_int(num, default=1):
	""" 转化为整形 """
	try:
		return int(num)
	except Exception, e:
		return default

def check_auth(username, password):
	""" 校验用户名和密码是否正确 """
	return username == 'admin' and password == 'secret'

def authenticate():
	""" Sends a 401 response that enables basic auth """
	return Response(
	'Could not verify your access level for that URL.\n'
	'You have to login with proper credentials', 401,
	{'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		if not auth or not check_auth(auth.username, auth.password):
			return authenticate()
		return f(*args, **kwargs)
	return decorated

page = Blueprint('user', __name__, template_folder='templates')

@page.route('/')
@login_required
def index():
	limit = 100
	page = to_int(request.args.get('page'))
	_type = request.args.get('_type')

	if current_user.role != 'root':
		created_by = current_user.id
		q = {'created_by': created_by}
		current_mananger = mongo.db.managers.find_one({'username': current_user.id})
		hint = '已使用语音授权：%s/%s，已使用siri授权：%s/%s，已使用匿名授权：%s/%s' % \
		(current_mananger['used_voice_licenses'], current_mananger['voice_licenses'],
			current_mananger['used_siri_licenses'], current_mananger['siri_licenses'],
			current_mananger.get('used_anonymous_licenses', 0), current_mananger.get('anonymous_licenses',0),)
	else:
		q = {}
		hint = ''
		created_by = None

	if _type:
		q['type'] = _type

	users = mongo.db.users.find(q).sort([('created_at', -1)]).skip(limit*(page-1)).limit(limit)
	total = mongo.db.users.count(q)
	pagination = Pagination(page=page, per_page=limit, total=total, record_name='users')
	return render_template('users/index.html', users=users, pagination=pagination, _type=_type, hint=hint)

@page.route('/user/new', methods=['GET'])
@login_required
def new():
	user = {}
	return render_template('users/new.html', user=user)

@page.route('/api/users', methods=['POST'])
def multiple_create():
	try:
		data = request.get_json()
		users = data.get('users')
		formatted_users = []
		for user in users:
			if user.get('type', '') == 'siri':
				user['udid'] += '-W'
			elif user.get('type', '') == 'anonymous':
				user['udid'] += '-V'
			user['status'] = True
			user['created_at'] = datetime.now()
			user['created_by'] = None
			formatted_users.append(user)
		mongo.db.users.insert(formatted_users)
		return jsonify({'code': 200})
	except Exception, e:
		return jsonify({'code': 500})

	

@page.route('/users', methods=['POST'])
@login_required
def create():
	try:
		form = request.form
		username = form['username'].strip()
		backup = form['backup']
		status = form['status']
		_type = form['type']
		udid = form['udid'].strip()
		created_at = datetime.now()

		if current_user.role != 'root':
			created_by = current_user.id
		else:
			created_by = None

		manager = mongo.db.managers.find_one({'username': current_user.id})

		if manager.get('enable') == False:
			# 管理被禁用
			flash('无操作权限')
			return redirect(url_for('user.index'))

		inc = {'used_licenses': 1}

		if _type == 'siri':
			udid = '%s-W' % udid
			if manager.get('role') != 'root':
				siri_licenses = manager.get('siri_licenses')
				used_siri_licenses = manager.get('used_siri_licenses')
				if siri_licenses <= used_siri_licenses:
					flash('siri授权数不足')
					return redirect(url_for('user.index'))
				inc['used_siri_licenses'] = 1
		elif _type == 'anonymous':
			udid = '%s-V' % udid
			if manager.get('role') != 'root':
				anonymous_licenses = manager.get('anonymous_licenses')
				used_anonymous_licenses = manager.get('used_anonymous_licenses')
				if anonymous_licenses <= used_anonymous_licenses:
					flash('匿名授权数不足')
					return redirect(url_for('user.index'))
				inc['used_anonymous_licenses'] = 1
		else:
			if manager.get('role') != 'root':
				voice_licenses = manager.get('voice_licenses')
				used_voice_licenses = manager.get('used_voice_licenses')
				if voice_licenses <= used_voice_licenses:
					flash('语音授权数不足')
					return redirect(url_for('user.index'))
				inc['used_voice_licenses'] = 1


		user = {
			'type': _type,
			'username': username,
			'backup': backup,
			'udid': udid,
			'status': status == 'true' and True or False,
			'created_at': created_at,
			'created_by': created_by,
		}

		user_id = mongo.db.users.insert_one(user).inserted_id

		mongo.db.managers.update({'username': current_user.id}, {'$inc': inc})
		return redirect(url_for('user.index'))
	except DuplicateKeyError:
		flash('udid重复')
		return redirect(url_for('user.index'))
	except Exception, e:
		flash(e)
		return redirect(url_for('user.index'))
		
@page.route('/user/update/<user_id>', methods=['POST'])
@login_required
def update(user_id):
	try:
		form = request.form 
		_type = form['type']
		username = form['username'].strip()
		backup = form['backup']
		status = form['status']
		udid = form['udid'].strip()

		if _type == 'siri':
			udid = '%s-W' % udid
		elif _type == 'anonymous':
			udid = '%s-V' % udid

		user = {
			'type': _type,
			'username': username,
			'udid': udid,
			'status': status == 'true' and True or False,
			'backup': backup,
		}

		result = mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': user})
	except DuplicateKeyError:
		flash('udid重复')
	except Exception, e:
		flash(e)
	finally:
		return redirect(url_for('user.index'))

@page.route('/user/edit/<user_id>', methods=['GET'])
@login_required
def edit(user_id):
	user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
	return render_template('users/edit.html', user=user)

@page.route('/user/delete/<user_id>', methods=['GET'])
@login_required
def delete(user_id):
	mongo.db.users.remove({'_id': ObjectId(user_id)})
	return redirect(url_for('user.index'))

@page.route('/user/statistics', methods=['GET'])
def statistics():
	"""统计"""
	total = mongo.db.users.count()

	condition = [
     	{ '$project': {'day': {'$dateToString': { 'format': "%Y-%m-%d", 'date': "$created_at" }}}},
     	{ '$group': {'_id': "$day", 'number': {'$sum': 1 }}},
     	{ '$sort': {'_id': -1}},
   	]

	result = mongo.db.users.aggregate(condition)

	return render_template('users/statistics.html', total=total, result=result) 

	


