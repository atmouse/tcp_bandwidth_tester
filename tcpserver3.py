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
from contextlib import contextmanager

#Dictionaries are thread safe. Threads might access old values depending on execution order,
#but corrupt values will not result. Also, in this case, each thread will only ever read from,
#or write to, a single thread.
global amount
global bandwidth
#global client_active
#global filename

@contextmanager
def closing(thing):
    try:
        yield thing
    finally:
        thing.close()

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
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)        
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
                #handle standard input
                line = sys.stdin.readline()
                print 'Press "quit" on the graphing window to quit the server.\n'

    #print 'Received signal to stop'

    #self.socket.close()

    #keys = bandwidth.keys()
    #new_line = ''
    #for i in keys:
    #    new_line += i + ' '

    #with closing(file(filename + '_header', 'w')) as f:
    #    f.write(new_line)

    #for c in self.threads:
    #    c.running = 0
    #    c.join()

class Client(threading.Thread): #client thread
  def __init__(self, (client, address)):
    threading.Thread.__init__(self) 
    self.client = client #the socket
    self.ip = address[0] #ip address
    self.size = 1024 #the message size
    self.username = None
    self.running = 1 #running state variable
    self.congestion = ''
    self.name = '' #uniquely identifies the client

  def run(self):

    #wait for client to indicate its type of congestion control
    data = self.client.recv(self.size)
    message = data.split(' ')
    self.congestion = message[1]
    print 'New client created.'
    print 'Type of Congestion Control: ' + self.congestion

    self.name = self.congestion + '-' + self.ip
    bandwidth[self.name] = 0
    amount[self.name] = 0
    #client_active[self.name] = 1

    self.client.send('* proceed ' + self.name)
    print 'New TCP ' + self.name + ' client will commence sending data.'

    while self.running:
        try:
          data = self.client.recv(self.size)
        except socket.error:
          #socket closed on receive
          pass

        if data:
            amount[self.name] += len(data)
        else:
            print 'TCP ' + self.name + ' client has terminated.'
            amount[self.name] = 0
            #client_active[self.name] = 0
            self.client.close() #close socket
            self.running = 0

class GraphWindow():

        def __init__(self, master, filename):
                #ion() #animated graphing

                # Instantiate figure and plot
                self.f = Figure(figsize=(5,4), dpi=100)

                #available colours for graphing
                self.colours = ['#FF0000', '#330000', '#339900', '#0066CC', '#990099']
                self.filename = filename

                self.ax1 = self.f.add_subplot(111, xlabel='Time (s)', ylabel='Throughput (MB)', xticks=[], yticks=arange(0, 300, 10))
                self.ax1.grid(True) #Show a grid on the plot axes
                self.max_y = 140
                self.ax1.axis(array([0, 100, 0, self.max_y]))
                self.x = arange(0, 100, 1)
                self.y = {} #dictionary of y-data as a list, and a line, stored together as a tuple

                # Instantiate canvas
                self.canvas = canvas = FigureCanvasTkAgg(self.f, master)

                # Pack canvas into root window
                canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
                # canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

                # Instantiate and pack toolbar
                self.toolbar = toolbar = NavigationToolbar2TkAgg(canvas, master)

                # Instantiate and pack quit button
                self.button = button = Tk.Button(master, text='Quit', command=sys.exit)
                button.pack(side=Tk.BOTTOM)

                # Show canvas and toolbar
                toolbar.update()
                canvas.show()

        def __call__(self):
                keys = bandwidth.keys()

                for i in keys:
                    try:
                        speed = bandwidth[i]
                        speed = speed / (1000 * 1000.)

                        #if i has not been added to the y data, the except block will add it.
                        self.y[i][0].pop(0)
                        self.y[i][0].append(speed)

                        with closing(file(self.filename + '_' + i, 'a')) as f:
                            f.write(str(bandwidth[i]) + '\n')

                        if speed > self.max_y:
                            self.max_y = speed
                            self.ax1.axis(array([0, 100, 0, self.max_y]))
                        self.y[i][1].set_ydata(self.y[i][0])
                    except KeyError:
                        y = []
                        while len(y) < 100:
                            y.append(0)
                        c = self.colours[-1]
                        self.colours.pop()
                        l, = self.ax1.plot(self.x, y, c)
                        self.ax1.axis(array([0, 100, 0, self.max_y]))
                        self.y[i] = (y, l)
                        self.y[i][1].set_ydata(y)
                        
                        lines = []
                        names = []
                        for i in self.y:
                            #if client_active[i] == 1:
                            y, l = self.y[i]
                            names.append(i)
                            lines.append(l)

                        self.ax1.legend(lines, names, 'upper left')
                        
                        #headers = ''
                        #for i in names:
                        #    headers += i + ' '
                        #with closing(file(filename + '_header', 'w')) as f:
                        #    f.write(headers)
                
                self.canvas.show()

class UpdatePlot(threading.Thread):
    def __init__(self, function):
        threading.Thread.__init__(self) 
        self.function = function
        self.running = 1

    def run(self):
        amount_now = {}
        while (self.running):
            start = 0 
            end = 0
            keys = bandwidth.keys()
            start = time.time()
            time.sleep(1)
            for i in keys:
                 amount_now[i] = amount[i]
                 amount[i] = 0
            end = time.time()
            #data = ''
            for i in keys:
                 bandwidth[i] = (amount_now[i]/(end - start))
                 #data += str(bandwidth[i]) + ' '
            #new_line = data + '\n'
            #using a context manager looks unseemly, but it in this case it prevents
            #a segmentation fault when the daemon thread is terminated
            #with closing(file(filename + '_data', 'a')) as f:
            #    f.write(new_line)
            self.function()

if __name__ == "__main__":

    amount = {}
    bandwidth = {}
    #client_active = {} 

    try:
      port = sys.argv[1]
      filename = sys.argv[2]
    except:
      print '<port> <filename>'
      #print '<port>'
      sys.exit(0)

    s = Server(int(port))
    t = threading.Thread(target = s.run)
    t.setDaemon(True)
    t.start()

    #graphing gui stuff
    root = Tk.Tk()
    root.wm_title("TCP Bandwidth Tester")
    graph = GraphWindow(root, filename)
    update = UpdatePlot(graph)
    update.setDaemon(True)
    update.start()

    Tk.mainloop()

