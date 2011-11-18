import matplotlib
matplotlib.use('TkAgg')
 
from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
 
import Tkinter as Tk
import sys
 
class App:

	def __init__(self, master):
		# Instantiate figure and plot
		self.f = Figure(figsize=(5,4), dpi=100)
		self.ax1 = self.f.add_subplot(311)
		self.ax2 = self.f.add_subplot(312)
                #self.ax3 = self.f.add_subplot(313)
                self.ax3 = None

                self.count = 0
 
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
 
	def __call__(self, x_axis, y_axis):
		# Do the plotting

                self.count += 1

		self.ax1.plot(x_axis, y_axis)
		self.ax2.plot(x_axis, -1 * y_axis)

                if self.count == 3:
                	print 'Now'
                        self.ax3 = self.f.add_subplot(313)
                        self.ax3.plot(x_axis, 2*y_axis)

		self.canvas.show()
 
if __name__ == "__main__":
	root = Tk.Tk()
	root.wm_title("Embedding in TK")
	app = App(root)
 
	def UpdatePlot():
		import time
		i = 1
		while True:
			t = arange(0.0,3.0,0.01)
			s = sin(2*pi*t)
			app(t, s * i)
			i += 1
			time.sleep(1)
 
	import threading
	t0 = threading.Thread(target=UpdatePlot)
	t0.start()
 
	Tk.mainloop()

        print 'this wont work'
