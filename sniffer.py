#!/usr/bin/env python2

'''
    Example code taken from http://pylibpcap.sourceforge.net/ which demonstrates
    a packet sniffer written in python using the python-libpcap wrapper for the 
    libpcap library.

    Modified heavily to suit my own need for a way to measure tcp round trip times
    without using ping or third party tools (besides the python wrapper for libpcap).

    Other links I found useful:
    http://systhread.net/texts/200805lpcap1.php
    http://www.tcpdump.org/pcap3_man.html
'''

import pcap
import sys
import string
import time
import socket
import struct

import fcntl

protocols={socket.IPPROTO_TCP:'tcp',
           socket.IPPROTO_UDP:'udp',
           socket.IPPROTO_ICMP:'icmp'}

dest_ip = ''
local_ip = ''

def get_ip_address(ifname):
  '''
     This method of obtaining the ip address of a machine was obtained from, and explained by
     http://code.activestate.com/recipes/439094-get-the-ip-address-associated-with-a-network-inter/
     Apparently, this will not work on all versions of linux.
     The reason I use this method is summed up pretty will on the website:

     A common way of the determining the "IP address of the computer" is just to use:
     socket.gethostbyname(socket.gethostname())
     This works well on Windows, and on unix hosts configured in the traditional way with their main
     ip address set in /etc/hosts. It won't return useful results on unix systems that have their 
     hostnames mapped to the loopback address in /etc/hosts, which is pretty common, but it's a 
     good platform independent fallback to use when no specific interface or address information 
     has been provided.
  '''
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])

def decode_ip_packet(s):
  d={}
  #d['version']=(ord(s[0]) & 0xf0) >> 4
  #d['header_len']=ord(s[0]) & 0x0f
  #d['tos']=ord(s[1])
  #d['total_len']=socket.ntohs(struct.unpack('H',s[2:4])[0])
  #d['id']=socket.ntohs(struct.unpack('H',s[4:6])[0])
  #d['flags']=(ord(s[6]) & 0xe0) >> 5
  #d['fragment_offset']=socket.ntohs(struct.unpack('H',s[6:8])[0] & 0x1f)
  #d['ttl']=ord(s[8])
  d['protocol']=ord(s[9])
  #d['checksum']=socket.ntohs(struct.unpack('H',s[10:12])[0])
  d['source_address']=pcap.ntoa(struct.unpack('i',s[12:16])[0])
  d['destination_address']=pcap.ntoa(struct.unpack('i',s[16:20])[0])
  #if d['header_len']>5:
  #  d['options']=s[20:4*(d['header_len']-5)]
  #else:
  #  d['options']=None
  #d['data']=s[4*d['header_len']:]

  #The difference between ntohs and ntohl is the difference between 16bit and 32bit integers.
  #d['source_port'] = socket.ntohs(struct.unpack('H',s[20:22])[0])
  #d['destination_port'] = socket.ntohs(struct.unpack('H',s[22:24])[0])
  d['sequence_number'] = socket.ntohl(struct.unpack('I',s[24:28])[0])
  d['ack_number'] = socket.ntohl(struct.unpack('I',s[28:32])[0])

  return d

def handle_packet(pktlen, data, timestamp):
  if not data:
    return

  if data[12:14]=='\x08\x00':
    decoded = decode_ip_packet(data[14:])
    print '\n%s.%f %s > %s' % (time.strftime('%H:%M',
                                           time.localtime(timestamp)),
                             timestamp % 60,
                             decoded['source_address'],
                             decoded['destination_address'])
    for key in ['sequence_number', 'ack_number']:
      print '  %s: %d' % (key, decoded[key])
    print '  protocol: %s' % protocols[decoded['protocol']]

if __name__=='__main__':
  if len(sys.argv) == 4:
    #dev = pcap.lookupdev()
    dev = sys.argv[1]
    expr = sys.argv[3:]
    dest_ip = sys.argv[2]
  else:
    print 'usage: <dev> <ip> <expr>'
    sys.exit(0)

  p = pcap.pcapObject()
  net, mask = pcap.lookupnet(dev)

  local_ip = get_ip_address(dev)
  print 'This machine\'s ip is: ' + str(local_ip)

  # note:  to_ms does nothing on linux
  p.open_live(dev, 1600, 0, 100)
  #p.dump_open('dumpfile')
  p.setfilter(string.join(expr,' '), 0, 0)

  # try-except block to catch keyboard interrupt.  Failure to shut
  # down cleanly can result in the interface not being taken out of promisc.
  # mode
  #p.setnonblock(1)
  try:
    while 1:
      p.dispatch(1, handle_packet)

    # specify 'None' to dump to dumpfile, assuming you have called
    # the dump_open method
    #  p.dispatch(0, None)

    # the loop method is another way of doing things
    #  p.loop(1, print_packet)

    # as is the next() method
    # p.next() returns a (pktlen, data, timestamp) tuple 
    #  apply(print_packet,p.next())
  except KeyboardInterrupt:
    print '%s' % sys.exc_type
    print 'shutting down'
    print '%d packets received, %d packets dropped, %d packets dropped by interface' % p.stats()

