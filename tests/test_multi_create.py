# encoding: utf-8

import requests

users = [
	{ "username" : "hailei", "udid" : "322C6EB6-812B-4506-8AB7-2AFA3A1271CF", "type" : "siri", 'backup': 'hailei' },
	# { "username" : "pengru", "udid" : "322C6EB6-812B-4506-8AB7-2AFA3A1271CF", "type" : "voice", 'backup': 'pengru' },
]

data = {'users': users}

url = 'http://127.0.0.1:5000/api/users'

response = requests.post(url, json=data)

print response.text
