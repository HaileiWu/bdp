# encoding: utf-8

from pymongo import MongoClient

client = MongoClient()

db = client.bdp

users = db.users.find()

for user in users:
	_id = user['_id'] 
	udid = user['udid']

	if udid[-2:] == '-W':
		_type = 'siri'
	else:
		_type = 'voice'

	db.users.update_one({'_id': _id}, {'$set': {'type': _type}})