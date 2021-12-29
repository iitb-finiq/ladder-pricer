# code to simulate the supplier
# each supplier sends the fix, ttl and start time to the middle server

import socket
from time import sleep	
from threading import Thread
from random import *
from jpype import *

# connect to a java jdk to get the time in nano seconds
# Can't use python functions as java has different seed for starting time
startJVM("C:/Program Files/Eclipse Adoptium/jdk-17.0.1.12-hotspot/bin/server/jvm.dll", "-ea")
javaPackage = JPackage("java.lang")
javaTimer = javaPackage.System.nanoTime
num_servers = 4 # number of suppliers to be created
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
    x = sr.recv(1024).decode().lower()
    while x != "started":
        x = sr.recv(1024).decode().lower()
        print(x)
        pass
    print("connected",id, javaTimer())
    
    # start sending fixes. Read the fixes from the file out.txt and then send 
    f = open("out.txt", "r")
    for _ in range(100000):             # CHANGE NUMBER OF FIXES HERE
        line = f.readline()
        if not line:
            f = open("out.txt") 
            line = f.readline()
        # sent_msg = Fix: fix;TTL:ttl;Start_Time:start_time### 
        fix = "Fix:" + str(line) + ";TTL:" + str(int(valid_period)) + ";Start_Time:" + str(javaTimer()) + "###"
        sr.send(fix.encode())
        sleep(gap_btw_fixes)

    # after sending the fixes, send "end" and close the server
    print(id, "server closing", javaTimer())
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