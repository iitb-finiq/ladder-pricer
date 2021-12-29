# code to simulate the client
# each client sends a particular request for a size and gets back the best price for that size for each supplier
from os import startfile
import socket	
from random import randint		
from threading import Thread
from jpype import *

num_clients = 10  # number of clients to be created
server_port = 12345
client_port = 1025
middle_port_client=2345		

# connect to a java jdk to get the time in nano seconds
# Can't use python functions as java has different seed for starting time
startJVM("C:/Program Files/Eclipse Adoptium/jdk-17.0.1.12-hotspot/bin/server/jvm.dll", "-ea")
javaPackage = JPackage("java.lang")
javaTimer = javaPackage.System.nanoTime

# function to create one client with id = id
def create_client(id):
    # Connecting to the socket 
    sr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
    sr.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sr.connect(('127.0.0.1', middle_port_client))

    # wait for confirmation
    f = open(f"data/o{id}", 'w')
    while sr.recv(1024).decode().lower() != "started":
        pass
    print("connected", id)
    totalT = 0
    notional = 0
    for _ in range(500):             # CHANGE NUMBER OF REQUESTS HERE
        # f.write(str(javaTimer()) + '\n')
        t1 = javaTimer()
        print(_)
        # notional=randint(1,1000)
        notional += 100
        # send the request to the server
        sr.send(f"Notional:{notional}".encode())
        # wait for the reply from the server. The reply contains the best price for each supplier
        s =sr.recv(8192).decode()
        log = f"{_}, {javaTimer()}, {notional}, {javaTimer() - t1}, {s}\n"
        f.write(log)
        totalT += javaTimer() - t1
        # print (_,notional, sr.recv(1024).decode())	
    f.close()
    print(totalT)
    # after sending the fixes, send "end" and close the client
    sr.send("end".encode())
    sr.close()

# create different threads for each client
t = [None]*num_clients
for _ in range(num_clients):
    t[_] = Thread(target=create_client, args=(_,))
    t[_].start()
    
# wait for all clients to end
for _ in range(num_clients):
    t[_].join()