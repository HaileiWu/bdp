# encoding: utf-8
import SocketServer
import sys
from gevent.server import StreamServer
import json
import traceback
import binascii
import time
import threading

from pymongo import MongoClient
from crypt import AESC, RSAC, RNC

client = MongoClient()

db = client.bdp

port = 6668

if len(sys.argv) > 1:
    port = int(sys.argv[1])

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
        time.sleep(0.01)
    except Exception, e:
    	pass
    finally:
        socket.close()

class RequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        """ 处理请求 """
        try:
            data = self.request.recv(1024)

            key = binascii.b2a_hex(data[0:16]).upper()

            body = data[16:]

            # RN解密
            rnc = RNC(key)
            data = rnc.decrypt(body)

            data = json.loads(data)
            
            usr = data['usr']
            udid = data['udid']
            
            #print 'request from %s' % usr
            
            user = db.users.find_one({'udid': udid})

            if user and user.get('status'):
                status = 1 
            else:
                status = 0

            # 2、查询mongo
            response = {'udid': udid, 'status': status}
            cipher_text = rnc.encrypt(json.dumps(response))
            self.request.send(cipher_text)

        except Exception, e:
            print e
            print self.request.send('')

class Server(SocketServer.TCPServer):
    pass
    

server_address = ('0.0.0.0', port)
# server = StreamServer(server_address, handle)
# server.serve_forever()

server = Server(server_address, RequestHandler)
server.serve_forever()




