# encoding: utf-8
import select
import socket
import sys
import Queue
import json
import traceback
import binascii

from pymongo import MongoClient
from crypt import AESC, RSAC, RNC

client = MongoClient()

db = client.bdp

class AuthorizeServer(object):
    """ Use for authorize """

    def __init__(self):
        # 创建TCP/IP socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)

        server_address = ('0.0.0.0', 10000)
        print >>sys.stderr, 'starting up on %s port %s' % server_address
        self.server.bind(server_address)

        # 要监听的连接数
        self.server.listen(50)

        # 要读取的Sockets
        self.inputs = [ self.server ]

        # 要写入的Sockets
        self.outputs = [ ]

        # Outgoing message queues (socket:Queue)
        self.message_queues = {}

    def handle(self, data):
        """ 处理请求 """

        key = binascii.b2a_hex(data[0:16]).upper()

        body = data[16:]

        # RN解密
        rnc = RNC(key)
        data = rnc.decrypt(body)

        data = json.loads(data)
        
        usr = data['usr']
        udid = data['udid']
        
        user = db.users.find_one({'username': usr, 'udid': udid})

        if user:
            status = True 
        else:
            status = False

        # 2、查询mongo
        response = {'udid': udid, 'status': status}
        cipher_text = rnc.encrypt(json.dumps(response))
        return cipher_text


    def run(self):
        """ start server """
        while self.inputs:
            try:
                # 阻塞等待处理的sockets
                print >>sys.stderr, '\nwaiting for the next event'
                readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)

                # 处理输入
                for s in readable:

                    if s is self.server:
                        # A "readable" server socket is ready to accept a connection
                        connection, client_address = s.accept()
                        print >>sys.stderr, 'new connection from', client_address
                        connection.setblocking(0)
                        self.inputs.append(connection)

                        # Give the connection a queue for data we want to send
                        self.message_queues[connection] = Queue.Queue()

                    else:
                        data = s.recv(1024)
                        if data:
                            # A readable client socket has data
                            print >>sys.stderr, 'received "%s" from %s' % (data, s.getpeername())

                            # handle request data
                            data = self.handle(data)

                            self.message_queues[s].put(data)
                            # Add output channel for response
                            if s not in self.outputs:
                                self.outputs.append(s)

                        else:
                            # Interpret empty result as closed connection
                            print >>sys.stderr, 'closing', client_address, 'after reading no data'
                            # Stop listening for input on the connection
                            if s in self.outputs:
                                self.outputs.remove(s)
                            self.inputs.remove(s)
                            s.close()

                            # Remove message queue
                            del self.message_queues[s]

                # Handle outputs
                for s in writable:
                    try:
                        next_msg = self.message_queues[s].get_nowait()
                    except Queue.Empty:
                        # No messages waiting so stop checking for writability.
                        print >>sys.stderr, 'output queue for', s.getpeername(), 'is empty'
                        self.outputs.remove(s)
                    else:
                        print >>sys.stderr, 'sending "%s" to %s' % (next_msg, s.getpeername())
                        s.send(next_msg)

                # Handle "exceptional conditions"
                for s in exceptional:
                    print >>sys.stderr, 'handling exceptional condition for', s.getpeername()
                    # Stop listening for input on the connection
                    self.inputs.remove(s)
                    if s in self.outputs:
                        self.outputs.remove(s)
                    s.close()

                    # Remove message queue
                    del self.message_queues[s]
            except Exception, e:
                print traceback.format_exc()


if __name__ == '__main__':
    server = AuthorizeServer()
    server.run()