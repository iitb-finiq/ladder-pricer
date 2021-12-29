# code to simulate the supplier
# each supplier sends the fix, ttl and start time to the middle server

import socket
from time import sleep, time_ns	
from threading import Thread
from random import *

num_servers = 10 # number of suppliers to be created
server_port = 12345
client_port = 1025
middle_port_server=3456				

# function to create one server with id = id
def create_server(id):
    gap_btw_fixes = 0.3 # time gap between 2 fixes
    valid_period = 1.2e9 # time to live for each fix

    # Connecting to the socket 
    sr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
    print ("Server Socket successfully created")
    sr.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sr.connect(('127.0.0.1', middle_port_server))

    # wait for confirmation
    while sr.recv(1024).decode().lower() != "started":
        pass
    print("connected",id, time_ns())

    # start sending fixes. Read the fixes from the file out.txt and then send
    f = open("out.txt", "r")
    for _ in range(10000):
        line = f.readline()
        if not line:
            f = open("out.txt") 
            line = f.readline()
        # sent_msg = Fix: fix;TTL:ttl;Start_Time:start_time 
        fix = "Fix:".encode() + str(line).encode() + ";TTL:".encode() + str(valid_period).encode() + ";Start_Time:".encode() + str(time_ns()).encode()
        sr.send(fix)
        line = f.readline()
        if not line:
            f = open("out.txt") 
        sleep(gap_btw_fixes)

    # after sending the fixes, send "end" and close the server
    print(id, "server closing", time_ns())
    sr.send("end".encode())
    sr.close()

# create different threads for each supplier
t = [None]*num_servers
for _ in range(num_servers):
    t[_] = Thread(target=create_server, args=(_,))
    t[_].start()

# wait for all servers to end
for _ in range(num_servers):
    t[_].join()