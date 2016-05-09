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
	else:
		created_by = None
	if _type == 'siri':
		users = mongo.db.users.find({'created_by': created_by, 'type': _type})
	elif _type == 'voice':
		users = mongo.db.users.find({'$and': [{'created_by': created_by}, {'$or': [{'type': None}, {'type': 'voice'}]}]})
	else:
		users = mongo.db.users.find({'created_by': created_by})

	total = mongo.db.users.count()
	pagination = Pagination(page=page, total=total, record_name='')
	return render_template('users/index.html', users=users, pagination=pagination, _type=_type)

@page.route('/user/new', methods=['GET'])
@login_required
def new():
	user = {}
	return render_template('users/new.html', user=user)

@page.route('/api/users', methods=['POST'])
def multiple_create():
	data = request.get_json()
	users = data.get('users')

	formatted_users = []
	for user in users:
		if user.get('type', '') == 'siri':
			user['udid'] += '-W'
		user['status'] = True
		user['created_at'] = datetime.now()
		user['created_by'] = None
		formatted_users.append(user)
	
	mongo.db.users.insert(formatted_users)

	return jsonify({'code': 200})

	

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

		if _type == 'siri':
			udid = '%s-W' % udid

		user = {
			'type': _type,
			'username': username,
			'backup': backup,
			'udid': udid,
			'status': status == 'true' and True or False,
			'created_at': created_at,
			'created_by': created_by,
		}

		manager = mongo.db.managers.find_one({'username': current_user.id})

		if manager.get('enable') == False:
			# 管理被禁用
			flash('无操作权限')
			return redirect(url_for('user.index'))

		licenses = manager.get('licenses')
		used_licenses = manager.get('used_licenses')

		if licenses <= used_licenses:
			flash('授权数不足，请联系管理员充值')
			return redirect(url_for('user.index'))

		user_id = mongo.db.users.insert_one(user).inserted_id

		mongo.db.managers.update({'username': current_user.id}, {'$inc': {'used_licenses': 1}})
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

@page.route('/user/statistics', methods=['GET'])
def statistics():
	"""统计"""
	total = mongo.db.users.count()

	condition = [
     	{ '$project': {'day': {'$dateToString': { 'format': "%Y-%m-%d", 'date': "$created_at" }}}},
     	{ '$group': {'_id': "$day", 'number': {'$sum': 1 }}},
   	]

	result = mongo.db.users.aggregate(condition)

	return render_template('users/statistics.html', total=total, result=result) 

	


