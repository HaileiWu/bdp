import socket
import sys
import json

from crypt import RSAC, AESC

key = 'm'*16
message = {'udid': 'x'*32, 'usr': 'c'*32, 'ck': key}



message = json.dumps(message)

rsac = RSAC()

message = rsac.encrypt(message)

message = '49e63b5522a54080a038bcb60ce0f9050301111bbd79975af244a26f792d5983097cfdb9f359401d308de762ab6363e28cac41428dbe26599878d124c2950dd77dc2144b7a75ba0c1a6b41ef7a5e11c45c596e3748392ee45f764b3d12b5c55ea6e93f794ec785fc0315797828c09d5f9bdadae054437d575092789811713a6901eb97394ccb984d9a6e88833b174e2782814ddb98a0665216df7da75199c19095ee'.decode('hex')

print message

messages = [ message ]


server_address = ('0.0.0.0', 10000)

# Create a TCP/IP socket
socks = [ socket.socket(socket.AF_INET, socket.SOCK_STREAM),
          socket.socket(socket.AF_INET, socket.SOCK_STREAM),
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
        print >>sys.stderr, '%s: received "%s"' % (s.getsockname(), data)
        if not data:
            print >>sys.stderr, 'closing socket', s.getsockname()
            s.close()


