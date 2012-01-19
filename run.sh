#!/bin/bash

#<src ip> <dest ip> <port> <congestion> <filename> <network interface> <num_packets>
gcc rtt4.c -o rtt4 -lpcap
./rtt4 "$6" "$1" "$2" "$7" "`basename $5`_`basename $4`-`basename $1`-rtt.txt" &
python tcpclient.py "$2" "$3" "$4"
pkill -9 rtt4
exit 0
