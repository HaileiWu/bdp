# encoding: utf-8

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
from functools import wraps

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

page = Blueprint('page', __name__, template_folder='templates')

@page.route('/users')
@requires_auth
def index():
	limit = 100
	page = to_int(request.args.get('page'))
	users = app.db.users.find()
	total = app.db.count()
	pagination = Pagination(page=page, total=total, record_name='')
	return render_template('users/index.html', users=users, pagination=pagination)
