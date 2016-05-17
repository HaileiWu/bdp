# encoding: utf-8

import requests

users = [
	{ "username" : "hailei_test", "udid" : "322C6EB6-812B-4506-8AB7-2AFA3AD271CF", "type" : "siri", 'backup': 'hailei' },
	{ "username" : "pengru_test", "udid" : "322C6EB6-812B-4506-8AB7-2AFEA1271CF", "type" : "voice", 'backup': 'pengru' },
]

data = {'users': users}

url = 'http://47.89.47.215/api/users'

response = requests.post(url, json=data)

print response.text