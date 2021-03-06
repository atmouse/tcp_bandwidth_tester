#!/usr/bin/env python

'''A TCP client for data transmission to server.'''

import socket
import sys
import select
import time

class TCP_Client:
    def __init__(self, ip, port, cong):
        self.host = ip
        self.port = port 
        self.size = 1024
        self.socket = None
        self.congestion = cong #congestion control to be used, also used to identify client

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try: 
                #set congestion conrol algorithm
                socket.TCP_CONGESTION = 13
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, self.congestion)
                temp = self.socket.getsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, 10)
                print 'Congestion control used for this TCP connection set to: ' + str(temp)
            except Exception, (value, message):
                print 'Cannot set socket option. The TCP client must be launched with sudo rights'

            self.socket.connect((self.host, self.port))

            #client identifies itself to server
            self.send("# " + self.congestion)

            #client waits for server reply
            data = self.socket.recv(self.size)
            message = data.split(' ')
            if message[1] == 'proceed' and message[2] != '':
                print 'Server acknowledges TCP ' + message[2] + '.'
                self.spam()
            else:
                print 'Server responded incorrectly: ' + str(message)

        except socket.error, (value, message):
          print "Error: " + message
          sys.exit(1)

    def close_socket(self):
        self.socket.close()

    def send(self, message):
        try:
          self.socket.send(message)
        except socket.error:
          print "Error, send request failed"
          self.socket.close()
          sys.exit(1)
         
    def spam(self):
      buff = 1024 * '\0'
      print "spamming server"
      while 1:
        try:
          self.send(buff)
          #time.sleep(0.01)
        except socket.error:
          print 'An error occurred!'
          return 

if __name__ == '__main__':

    try:
        ip = sys.argv[1]
        host = sys.argv[2]
        congestion = sys.argv[3]
    except IndexError:
        print '<ip> <port> <congestion control>'
        sys.exit(0)

    print "Starting TCP client"

    c = TCP_Client(ip, int(host), congestion)
    c.start()
