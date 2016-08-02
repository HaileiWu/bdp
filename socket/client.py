import socket
import sys
import json

from crypt import RSAC, AESC, RNC

key = 'm'*16
message = { "usr" : "ver_Db", "udid" : "322C6EB6-812B-4506-8AB7-2AFA3A1271CF"}

rnc = RNC('DDF7D53D29FE46EBBB076BB9C40ABA07')

message = json.dumps(message)

rsac = RSAC()

message = rsac.encrypt(message)

message = 'ddf7d53d29fe46ebbb076bb9c40aba070301c4ac4e59eb26a1d5c2f990d67ba7670dd4fa8e1a155687c1685736b97d061e71dacb9eaa6fc1846de05bca1c8e431b3bd29364ba8767be26a4ce7304832d9e30eecf075b88687ad97b7fa529ed1f9c28d2bf8aef18c795e9fbbd222a671e524ec70f7e5b056bb003cc07e123d89ce561d32c2e5ab133c105d67ace198cd4b60cbaf7fba283579025f0bb971c8dcfe3cd'.decode('hex')

messages = [ message ]

# 47.89.47.215

server_address = ('127.0.0.1', 6666)

# Create a TCP/IP socket
socks = [ socket.socket(socket.AF_INET, socket.SOCK_STREAM),
          # socket.socket(socket.AF_INET, socket.SOCK_STREAM),
          ]

# Connect the socket to the port where the server is listening
print >>sys.stderr, 'connecting to %s port %s' % server_address
for s in socks:
    s.connect(server_address)


for message in messages:

    # Send messages on both sockets
    for s in socks:
        print >>sys.stderr, '%s: sending "%s"' % (s.getsockname(), message)
        s.send(message)

    # Read responses on both sockets
    for s in socks:
        data = s.recv(1024)
        print rnc.decrypt(data)
        print >>sys.stderr, '%s: received "%s"' % (s.getsockname(), data)
        if not data:
            print >>sys.stderr, 'closing socket', s.getsockname()
            s.close()


