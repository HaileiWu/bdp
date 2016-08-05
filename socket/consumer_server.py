# encoding: utf-8
import sys
import json
import traceback
import binascii
from  multiprocessing import Process
import gevent
import zmq.green as zmq

from gevent.server import StreamServer
from pymongo import MongoClient
from crypt import AESC, RSAC, RNC
from config import mongo_url

port = "6666"

if len(sys.argv) > 1:
    port = sys.argv[1]

context = zmq.Context()

def server(port=port):
    client = MongoClient(mongo_url)
    db = client.bdp
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:%s' % port)
    print 'running server on port: %s' % port
    while True:
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
            
            print '%s: request from %s' % (port, usr)

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
        	print e

if __name__ == '__main__':
    server_ports = range(6668, 6671)
    for server_port in server_ports:
        Process(target=server, args=(server_port,)).start()

# gevent.joinall([gevent.spawn(server)])