import matplotlib
matplotlib.use('TkAgg')
 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
 
import Tkinter as Tk
import sys
import time

from pylab import *
from numpy import *

class GraphWindow():

        def __init__(self, master, filename):

                # Instantiate figure and plot
                self.f = Figure(figsize=(5,4), dpi=100)
                self.filename = filename

                #available colours for graphing
                self.colours = ['#FF0000', '#330000', '#339900', '#0066CC', '#990099']

                self.ax1 = self.f.add_subplot(111, xlabel='Time (s)', ylabel='Throughput (MB)', xticks=[])
                self.ax1.grid(True) #Show a grid on the plot axes
                #self.max_y = 140
                #self.ax1.axis(array([0, 100, 0, self.max_y]))
                #self.x = arange(0, 100, 1)

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

                f = open(self.filename + '_header')
                headers = f.readline().split(' ')
                print headers
                f.close()
                num_headers = len(headers) - 1
    
                y = []
                for i in xrange(0, num_headers):
                    y.append([])

                f = open(self.filename + '_data')
                for line in f:
                    new_line = line.split(' ')
                    #print new_line
                    for i in xrange(0, num_headers):
                        try:
                            #y[i].append(new_line[i])
                            num = new_line[i]
                            if num == '\n':
                                y[i].append(0)
                            else: y[i].append(float(num))
                        except IndexError:
                            y[i].append(0)

                f.close()

                num_y_values = len(y[0])
                x = arange(0, num_y_values, 1)

                lines = []
                for y_data in y:
                    c = self.colours[-1]
                    self.colours.pop()
                    line = self.ax1.plot(x, y_data, c)
                    self.canvas.show()
                    time.sleep(5)
                    lines.append(line)
                names = headers[:len(headers)-1]
                self.ax1.legend(lines, names, 'upper left')
                self.canvas.show()

if __name__ == '__main__':

    try:
      filename = sys.argv[1]
    except:
      print '<filename>'
      sys.exit(0)

    #graphing gui stuff
    root = Tk.Tk()
    root.wm_title("TCP Bandwidth Tester")
    graph = GraphWindow(root, filename)
    graph()
    Tk.mainloop()
   
