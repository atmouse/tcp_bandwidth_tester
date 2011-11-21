#!/usr/bin/env python

'''
    A TCP server for receiving data from client.
    
    Code for gui-thread interaction based heavily on examples as found at
    https://www.esclab.tw/wiki/index.php/Matplotlib#Asynchronous_plotting_with_threads
'''

import matplotlib
matplotlib.use('TkAgg')
 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
 
import Tkinter as Tk
import sys 

from pylab import *
from numpy import *

import select
import socket
import threading
import time

#Dictionaries are thread safe. Threads might access old values depending on execution order,
#but corrupt values will not result. Also, in this case, each thread will only ever read from,
#or write to, a single thread.
global amount
global bandwidth

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
                c.setDaemon(True) #TODO true or false?
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

class Client(threading.Thread): #client thread
  def __init__(self, (client, address)):
    #key is the specific congestion control algorithm this client is associated with.
    threading.Thread.__init__(self) 
    self.client = client #the socket
    self.size = 1024 #the message size
    self.username = None
    self.running = 1 #running state variable
    self.key = ''

  def run(self):

    #wait for client to indicate its type of congestion control
    data = self.client.recv(self.size)
    message = data.split(' ')
    self.key = message[1]
    print 'New client created.'
    print 'Type of Congestion Control: ' + self.key

    #check if a client of this key type already exists
    value = bandwidth.get(self.key, -1)
    if value == -1:
        #client of this type does not already exist
        bandwidth[self.key] = 0
        amount[self.key] = 0
    else:
        #client of this type already exists
        print 'Additional TCP ' + self.key + ' client connected.'

    self.client.send('* proceed ' + self.key)
    print 'New TCP ' + self.key + ' client will commence sending data.'

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
            self.client.close() #close socket
            self.running = 0

class GraphWindow():

        def __init__(self, master):
                # Instantiate figure and plot
                self.f = Figure(figsize=(5,4), dpi=100)
                self.legend = False

                #available colours for graphing
                self.colours = ['#FF0000', '#330000', '#339900', '#0066CC', '#990099']

                self.ax1 = self.f.add_subplot(111)
                self.x = arange(0, 100, 1)
                self.y = {} #dictionary of y-data as a list, and graph colour, stored together as a tuple

                # Instantiate canvas
                self.canvas = canvas = FigureCanvasTkAgg(self.f, master)

                # Pack canvas into root window
                canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
                # canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

                # Instantiate and pack toolbar
                self.toolbar = toolbar = NavigationToolbar2TkAgg(canvas, master)

                # Instantiate and pack quit button
                #self.button = button = Tk.Button(master, text='Quit', command=sys.exit)
                #button.pack(side=Tk.BOTTOM)

                # Show canvas and toolbar
                toolbar.update()
                canvas.show()

        def __call__(self):
                keys = bandwidth.keys()
                self.ax1.clear()
                self.legend = True

                line_handle = []

                for i in keys:
                    try:
                        speed = bandwidth[i]/(1000*1000) 
                        self.y[i][0].pop(0)
                        self.y[i][0].append(speed)
                        l = self.ax1.plot(self.x, self.y[i][0], self.y[i][1])
                        line_handle.append(l)
                    except KeyError:
                        y = []
                        while len(y) < 100:
                            y.append(0)
                        c = self.colours[0]
                        self.colours.pop(0)
                        self.y[i] = (y, c)
                        self.legend = False
                        l = self.ax1.plot(self.x, self.y[i][0], self.y[i][1])

                if len(keys) > 1 and self.legend:
                    self.ax1.legend(line_handle, keys, 'upper left')
                 
                self.canvas.show()

class UpdatePlot(threading.Thread):
    def __init__(self, function):
        threading.Thread.__init__(self) 
        self.function = function
        self.running = 1

    def run(self):
        while (self.running):
            start = 0 
            end = 0
            amount_now = {}
            keys = bandwidth.keys()
            start = time.time()
            time.sleep(1)
            for i in keys:
                 amount_now[i] = amount[i]
                 amount[i] = 0
            end = time.time()
            for i in keys:
                 bandwidth[i] = amount_now[i]/(end - start)
            self.function()

if __name__ == "__main__":

    amount = {}
    bandwidth = {}
  
    try:
      port = sys.argv[1]
    except:
      print '<port>'
      sys.exit(0)

    s = Server(int(port))
    t = threading.Thread(target = s.run)
    t.setDaemon(False)
    t.start()

    #graphing gui stuff
    root = Tk.Tk()
    root.wm_title("Embedding in TK")
    graph = GraphWindow(root)
    update = UpdatePlot(graph)
    update.start()

    Tk.mainloop()

