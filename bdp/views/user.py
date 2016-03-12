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

	if current_user.role != 'root':
		created_by = current_user.id
	else:
		created_by = None

	users = mongo.db.users.find({'created_by': created_by})

	total = mongo.db.users.count()
	pagination = Pagination(page=page, total=total, record_name='')
	return render_template('users/index.html', users=users, pagination=pagination)

@page.route('/user/new', methods=['GET'])
@login_required
def new():
	user = {}
	return render_template('users/new.html', user=user)


@page.route('/users', methods=['POST'])
@login_required
def create():
	try:
		form = request.form
		username = form['username'].strip()
		backup = form['backup']
		status = form['status']
		udid = form['udid'].strip()
		created_at = datetime.now()

		if current_user.role != 'root':
			created_by = current_user.id
		else:
			created_by = None

		user = {
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
		username = form['username'].strip()
		backup = form['backup']
		status = form['status']
		udid = form['udid'].strip()

		user = {
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
