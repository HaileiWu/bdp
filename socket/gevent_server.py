# encoding: utf-8
from gevent.server import StreamServer
import json
import traceback
import binascii

from pymongo import MongoClient
from crypt import AESC, RSAC, RNC

client = MongoClient()

db = client.bdp

def handle(socket, address):
    """ 处理请求 """
    try:
        data = socket.recv(1024)

        key = binascii.b2a_hex(data[0:16]).upper()

        body = data[16:]

        # RN解密
        rnc = RNC(key)
        data = rnc.decrypt(body)

        data = json.loads(data)
        
        usr = data['usr']
        udid = data['udid']
        
        print 'request from %s' % usr

        user = db.users.find_one({'udid': udid})

        if user and user.get('status'):
            status = 1 
        else:
            status = 0

        # 2、查询mongo
        response = {'udid': udid, 'status': status}
        cipher_text = rnc.encrypt(json.dumps(response))
        socket.send(cipher_text)
    except Exception, e:
    	pass
    finally:
        socket.close()
    

server_address = ('0.0.0.0', 6666)
server = StreamServer(server_address, handle)
server.serve_forever()




