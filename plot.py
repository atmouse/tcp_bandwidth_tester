#!/usr/bin/env python

import matplotlib
matplotlib.use('TkAgg')
 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
 
import Tkinter as Tk
import sys
import time
import os

from pylab import *
from numpy import *

class GraphWindow():

        def __init__(self, master, filename, data_files):

                # Instantiate figure and plot
                self.f = Figure(figsize=(5,4), dpi=100)
                self.data_files = data_files
                self.filename = filename

                #available colours for graphing
                self.colours = ['#FF0000', '#330000', '#339900', '#0066CC', '#990099']

                self.ax1 = self.f.add_subplot(111, xlabel='Time (s)', ylabel='Throughput (MB)', yticks=arange(0, 300, 10))
                self.ax1.grid(True) #Show a grid on the plot axes

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

                data = []

                for i in self.data_files:
                    f = open(i, 'r')
                    data.append([])
                    for line in f:
                        data[-1].append(float(line.strip()))
                    f.close()

                max_length = 0
                for i in data:
                    if max_length < len(i):
                        max_length = len(i)

                for i in xrange(len(data)):
                    data[i] = array(data[i])/(1000*1000.)
                    if len(data[i]) < max_length:
                        diff = max_length - len(data[i])
                        data[i] = hstack((zeros(diff), data[i]))

                x = arange(0, max_length, 1)

                lines = []
                for y_data in data:
                    c = self.colours[-1]
                    self.colours.pop()
                    line = self.ax1.plot(x, y_data, c)
                    lines.append(line)
                names = [i[len(filename)+1:] for i in data_files]
                self.ax1.legend(lines, names, 'upper left')
                self.canvas.show()

if __name__ == '__main__':

    try:
        filename = sys.argv[1]
    except:
        print '<filename>'
        sys.exit(0)

    listing = os.listdir(os.getcwd())
    data_files = []

    for i in listing:
        if (filename in i[:len(filename)]):
            data_files.append(i)

    if not (len(data_files) > 0):
        print 'No data files with the specified filename found'
        sys.exit(0)

    #graphing gui stuff
    root = Tk.Tk()
    root.wm_title("TCP Bandwidth Tester")
    graph = GraphWindow(root, filename, data_files)
    graph()
    Tk.mainloop()
   
