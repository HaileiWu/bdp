# encoding: utf-8

import os
import sys
import inspect
import glob

from importlib import import_module
from flask import Flask
from flask import render_template
from flask.ext.pymongo import PyMongo

from flask.ext import login as flask_login

reload(sys)
sys.setdefaultencoding("utf-8")

app = Flask(__name__, instance_relative_config=True)
mongo = PyMongo(app)

app.secret_key = 'boomshakala@hh,boomfucklak。。'

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "manager.login"
login_manager.login_message = '登录进入系统...'

# 配置信息
# app.config.from_object('camelia_backend.settings')
# app.config.from_pyfile('application.py', silent=True)


def _blueprints():
	""" 加载所有蓝图 """
	current_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
	views = glob.glob(os.path.join(current_path, 'views', '*.py'))
	modules = map(lambda x: '{0}.{1}'.format('bdp.views', os.path.splitext(os.path.basename(x))[0]), views)
	for module in modules:
		module = import_module(module)
		if hasattr(module, 'page'):
			page = getattr(module, 'page')
			app.register_blueprint(page)

_blueprints()






