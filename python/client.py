# code to simulate the client
# each client sends a particular request for a size and gets back the best price for that size for each supplier

from os import startfile
import socket	
from random import randint		
from time import time_ns
from threading import Thread

num_clients = 5 # number of clients to be created
server_port = 12345
client_port = 1025	
middle_port_client=2345		

# function to create one client with id = id
def create_client(id):
    # Connecting to the socket 
    sr = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
    sr.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sr.connect(('127.0.0.1', middle_port_client))

    # wait for confirmation
    f = open(f"o{id}", 'w')
    while sr.recv(1024).decode().lower() != "started":
        pass
    print("connected", id)

    totalT = 0
    for _ in range(300):
        # f.write(str(time_ns()) + '\n')
        t1 = time_ns()
        print(_)
        # send the request to the server
        notional=randint(1,1000)
        sr.send(f"Notional:{notional}".encode())
        # wait for the reply from the server. The reply contains the best price for each supplier
        s =sr.recv(8192).decode()
        log = f"{_}, {time_ns()}, {notional}, {s}\n"
        f.write(log)
        totalT += time_ns() - t1
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