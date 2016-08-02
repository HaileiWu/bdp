# encoding: utf-8
import json
import traceback
import binascii
import zmq

from gevent.server import StreamServer
from pymongo import MongoClient
from crypt import AESC, RSAC, RNC
from config import server_addresses

client = MongoClient()

db = client.bdp

def init_global_connect():
    """ 初始化连接 """
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    for address in server_addresses:
        socket.connect(address)
    return socket

balance = init_global_connect()

def distribute_handler(socket, address):
    try:
        data = socket.recv(1024)
        balance.send(data)
        cipher_text = balance.recv()
        socket.send(cipher_text)
    except Exception, e:
        pass
    finally:
        socket.close()

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
server = StreamServer(server_address, distribute_handler)
server.serve_forever()

# for request in range(1, 10):
#     balance.send('Hello')
#     message = balance.recv()
#     print message


