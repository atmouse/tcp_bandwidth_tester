#!/bin/bash

#<src ip> <dest ip> <port> <congestion> <filename> <network interface> <num_packets>
python tcpclient.py "$2" "$3" "$4" &
gcc rtt4.c -o rtt4 -lpcap
./rtt4 "$6" "$1" "$2" "$7" "`basename $5`_`basename $4`_`basename $1`_rtt.txt" &
