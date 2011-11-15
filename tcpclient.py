#!/usr/bin/env python

'''A TCP client for data transmission to server.'''

import socket
import sys
import select

class TCP_Client:
    def __init__(self, ip, port):
        self.host = ip
        self.port = port 
        self.size = 1024
        self.socket = None
        self.username = ''

    def open_socket(self):
        try:
          self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          self.socket.connect((self.host, self.port))
        except socket.error:
          print "Error, server refused connection"
          sys.exit(1)

    def close_socket(self):
        self.socket.close()

    def send(self, message):
        try:
          self.socket.send(message)
        except socket.error:
          print "Error, send request failed"
          sys.exit(1)
         
    def spam(self):
      buff = 1024 * '\0'
      print "spamming server"
      while 1:
        try:
          self.send(buff)
        except socket.error:
          print 'An error occurred!'
          return 

if __name__ == '__main__':

    try:
        ip = sys.argv[1]
        host = sys.argv[2]
    except IndexError:
        print '<ip> <port>'
        sys.exit(0)

    print "Starting TCP client"

    c = TCP_Client(ip, int(host))
    c.open_socket()
    c.spam() 
