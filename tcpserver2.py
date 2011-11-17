#!/usr/bin/env python

'''A TCP server for receiving data from client.'''

from pylab import *
from numpy import *

import select
import socket
import sys
import threading
import os
import pickle
import time
import datetime

#Dictionaries are thread safe. Threads might access old values depending on execution order,
#but corrupt values will not result. Also, in this case, each thread will only ever read from,
#or write to, a single thread.
global amount

def isOpen(ip,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      s.connect((ip, port))
      s.shutdown(2)
    except:
      print 'port '+str(port)+' blocked'

class Server:
  def __init__(self, port):
    self.host = ''
    self.port = port 
    self.backlog = 5
    self.size = 1024
    self.socket = None
    self.threads = []

  def open_socket(self):
    try:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        a = self.socket.bind((self.host, self.port))
        b = self.socket.listen(self.backlog)
    except socket.error, (value, message):
        if self.socket:
            self.socket.close()
        print "Could not open socket: " + message
        sys.exit(1)

  def run(self):
    self.open_socket()
    input = [self.socket, sys.stdin]
    running = 1

    while running:
        inputready, outputready, exceptready = select.select(input, [], [])

        for s in inputready:

            if s == self.socket:
                c = Client(self.socket.accept())
                c.setDaemon(True)
                c.start()
                self.threads.append(c)

            elif s == sys.stdin:
                # handle standard input
                line = sys.stdin.readline()
                if line.strip() == 'q':
                  running = 0
                else:
                  print "Type 'q' to stop the server"

    print 'Received signal to stop'

    self.socket.close()

    for c in self.threads:
        c.running = 0
        c.join()

class BandwidthMonitor(threading.Thread):
  def __init__(self, key):
    #key, is the specific congestion control algorithm this bandwidth monitor is associated with. 
    self.start = 0
    self.end = 0
    self.amount_now = 0
    self.key = key

  def initiate(self):
    self.start = time.time()

  def terminate(self):
    self.amount_now = amount[self.key]
    amount[self.key] = 0
    self.end = time.time()

  def get_bandwidth(self):
    return self.amount_now/(self.end-self.start)

class Client(threading.Thread): #client thread
  def __init__(self, (client, address)):
    #key is the specific congestion control algorithm this client is associated with.
    threading.Thread.__init__(self) 
    self.client = client #the socket
    self.address = address #the address
    self.size = 1024 #the message size
    self.username = None
    self.running = 1 #running state variable
    self.key = ''

  def run(self):

    #TODO wait for client to indicate its type of congestion control
    data = self.client.recv(self.size)
    print 'Type of Congestion Control: ' + data
    #TODO self.key = ...
    amount[key] = 0

    #TODO create a new bandwidth monitor thread
    #TODO create a new graphing thread

    #TODO Signal client to start sending data.

    while self.running:
        try:
          data = self.client.recv(self.size)
        except socket.error:
          #socket closed on receive
          pass

        if data:
            amount[self.key] += len(data)
        else:
            amount[self.key] = 0
            self.client.close()
            self.running = 0

if __name__ == "__main__":

  amount = {}
  
  try:
    port = sys.argv[1]  
  except:
    print '<port>'
    sys.exit(0)

  s = Server(int(port))
  t = threading.Thread(target = s.run)
  t.setDaemon(False)
  t.start()
  print 'Starting Bandwidth monitor'

  b = BandwidthMonitor()    
  x = arange(0,100,1)
  y = []
   
  ion() #animated graphing

  while len(y) < 100:
    y.append(0)

  current_speed = 140
  line, = plot(x,y,'g')
  axis(array([0, 100, 0, current_speed]))

  xticks([])
  grid('on')
  title('TCP')
  ylabel('Throughput (MB)')
  xlabel('Time (s)')

  axis(array([0, 100, 0, 200]))

  while 1:
    b.initiate()
    time.sleep(1)
    b.terminate()
    speed = b.get_bandwidth()/(1000*1000) 

    if speed > current_speed:
        current_speed = speed + 40
	axis(array([0, 100, 0, current_speed]))

    print str(speed) + ' MBytes/second'
    y.pop(0)
    y.append(speed)
    line.set_ydata(y)
    draw()
