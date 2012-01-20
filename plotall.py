#!/usr/bin/env python

"""
    usage: python plotall.py <save directory> <compute mean (0 or 1)> <name prefix1> <name prefix 2> and so on
"""

from matplotlib import pyplot as plt
import sys
import os
from pylab import*
from numpy import*

def plot(data_files, directory, compute_mean):
    print data_files

    fig = plt.figure()
    colours = ['#FF0000', '#330000', '#339900', '#0066CC', '#990099']
    ax1 = fig.add_subplot(111, xlabel='Time (s)', ylabel='Throughput (Mbps)', yticks=arange(0, 1000, 10))
    plt.grid(True) #Show a grid on the plot axes

    data = []
    for i in data_files:
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
        data[i] = array(data[i]) * 8. / (10**6)
        if len(data[i]) < max_length:
            diff = max_length - len(data[i])
            data[i] = hstack((zeros(diff), data[i]))

    x = arange(0, max_length, 1)

    lines = []
    for y_data in data:
        c = colours[-1]
        colours.pop()
        line, = plt.plot(x, y_data, c)
        lines.append(line)
    name = data_files[0].split("_")[0]

    if compute_mean:
        mean_values = []
        for y_data in data:
            mean_values.append(mean(y_data[diff:]))
        #names = [i[len(name)+1:] for i in data_files]
        names = []
        for i in xrange(len(data_files)):
            names.append(data_files[i][len(name)+1:] + " : " + str(floor(mean_values[i])) + " Mbps")
        plt.legend(lines, names, 'upper left')
    else:
        names = [i[len(name)+1:] for i in data_files]
        plt.legend(lines, names, 'upper left')

    #plt.show()

    fig.savefig(d + "/" + name + ".png")

if __name__ == "__main__":

    num_args = len(sys.argv)
    filenames = []
    listing = os.listdir(os.getcwd())

    d = os.path.dirname(sys.argv[1] + "/")
    if not os.path.exists(d):
        print "Creating directory " + d
        os.makedirs(d)
    else:
         if os.path.isdir(d):
            print "Directory already exists"
         else:
            print "Creating directory " + d
            os.makedirs(d)

    pairs = {}
    compute_mean = int(sys.argv[2])
    for i in xrange(3, num_args):
        filenames.append(sys.argv[i])

    for i in listing:

        if os.path.isdir(i):
            print i + " is a directory"
            continue

        for j in filenames:
            if (j in i[:len(j)]):
                value = i
                key = value.split("_")[0]
                pairs.get(key, -1)
                if not (key in pairs):
                    pairs[key] = []
                pairs[key].append(value)
    
    for v in pairs.values():
        plot(v, d, compute_mean)
        #break
