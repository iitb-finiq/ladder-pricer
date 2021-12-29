import socket
import select
from time import time, sleep, time_ns
from jpype import *
from queue import Queue
import signal
from threading import Lock, Thread
from sortedcontainers import SortedList
from multiprocessing import Process

def getPrice(javaObj, notional, s, t, resultdict, l):
    if t < time_ns():
        return
    val = javaObj.getBestPrice(notional)
    l.acquire()
    if resultdict[s]["Price"] < val:
        resultdict[s]["Price"] = val
        resultdict[s]["Time"] = t
    l.release()

def createjavaObject(fix, object):
    object["object"] = javaBidPricer()
    object["object"].parseFix(fix)

valid_period = 0.2
new_request_timeout = 0
startJVM("C:/Program Files/Eclipse Adoptium/jdk-17.0.1.12-hotspot/bin/server/jvm.dll", "-ea")
javaPackage = JPackage("BidPricer")
javaBidPricer = javaPackage.BidPricer
ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)		
mss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    

def start_server():
    ss.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    mss.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print ("Middle Socket successfully created")

    middle_port_client = 2345
    middle_port_server=3456

    ss.bind(('', middle_port_client))	
    print ("Middle socket (client) binded to %s" %(middle_port_client))
    mss.bind(('',middle_port_server))
    print ("Middle socket (server) binded to %s" %(middle_port_server))

    ss.listen(5)	
    mss.listen(5)
    print ("Middle (client) socket is listening")	

def handle_Server_response(response):
    if response.lower() == "end":
        return True, {}
    response = response.split(";")
    response = map(lambda x: x.split(":",1), response)
    r = {x[0].lower():x[1] for x in response}
    return False, r

def handle_server(connection, queue, id):
    connection.send(str.encode("Started"))
    while True:
        response=connection.recv(8192).decode()
        is_end, resp = handle_Server_response(response)
        if is_end:
            connection.close()
            
            print("server closing")
            return

        while "fix" not in resp:
            response=connection.recv(8192).decode()
            is_end, resp = handle_Server_response(response)
            if is_end:
                connection.close()
                print("server closing")
                return   
        queue.put(resp)

def handle_client(connection, queue_in, queue_out, id):
    connection.send(str.encode("Started"))
    while True:
        client_response = connection.recv(1024).decode().split(":",1)
        if client_response[0].lower() == "end":
            connection.close()
            return
        while client_response[0].lower() != "notional":
            client_response = connection.recv(1024).decode().split(":",1)
            if client_response[0].lower() == "end":
                connection.close()
                return
        notional=float(client_response[1])
        queue_out.put(notional)
        bestPrice = queue_in.get()
        connection.sendall(bestPrice.encode())
        # connection.sendall(f"Price:{bestPrice}".encode())

start_server()
server_id = 0
server_queues = {}
server_threads = {}
client_id = 0
client_queues = {}
client_threads = {}
serverObj = {}
rem_list_server = []
rem_list_client = []
time_i = 0
while True:
    t1 = time_ns()
    readable, writable, errored = select.select([mss, ss],[],[], new_request_timeout)
    # print("checked readable")
    t2 = time_ns()
    for s in readable:
        if s is mss:
            c1,addr1=s.accept()
            q = Queue()
            server_queues[server_id] = q
            server_threads[server_id] = Thread(target = handle_server, args = (c1, q, server_id,))
            server_threads[server_id].start()
            server_id+=1
        else:
            c, addr = s.accept()
            q1 = Queue()
            q2 = Queue()
            client_queues[client_id] = [q1,q2]
            client_threads[client_id] = Thread(target = handle_client, args = (c, q1, q2, client_id,))
            client_threads[client_id].start()
            client_id+=1
    t3 = time_ns()
    # print("created new available connections")
    for s in server_queues: 
        if not server_threads[s].is_alive():
            del server_threads[s]
            rem_list_server.append(s)
            continue
        if s in serverObj:
            # print(time_ns()/1e9, s, len(serverObj[s]), file=sys.stderr)
            i = serverObj[s].bisect_key_left(time_ns())
            del serverObj[s][:i]
            # serverObj[s] = list(filter(lambda x: time_ns() <= x["end_time"], serverObj[s]))
        while not server_queues[s].empty():
            try:
                response = server_queues[s].get(block=False)
            except:
                continue
            response.setdefault("ttl", valid_period)
            response["end_time"] = float(response.setdefault("start_time", time_ns()))+float(response["ttl"])
            if time_ns() > response["end_time"]:
                continue
            if s not in serverObj:
                serverObj[s] = SortedList([], key=lambda x: x[0])
            # serverObj[s].append(response.copy())
            response["thread"] = Thread(target = createjavaObject, args=(response["fix"], response))
            response["thread"].start()
            response["thread_joined"] = False
            serverObj[s].add([response["end_time"], response])
    
    # print("checked new fixes")
    t2=t3=t4=t5=t6=0
    for c in client_queues:
        t2 = time_ns()
        if not client_threads[c].is_alive():
            del client_threads[c]
            rem_list_client.append(c)
            continue
        t3 = time_ns()
        if not client_queues[c][1].empty():
            # print(c)
            try:
                notional = client_queues[c][1].get(block=False)
            except:
                continue
            t4 = time_ns()
            best_prices = {}
            for s,resp_list in serverObj.items():
                l = Lock()
                best_prices[s] = {"Price": -1}
                for end_time, resp in resp_list:
                    if not resp["thread_joined"]:
                        resp["thread"].join()
                        resp["thread_joined"] = True
                    resp["thread"] = Thread(target=getPrice, args=(resp["object"],notional, s, resp["end_time"], best_prices, l))
                    resp["thread"].start()
            # print(best_prices)
            t5 = time_ns()
            for s,resp_list in serverObj.items():
                for _,resp in resp_list:
                    resp["thread"].join()
            
            resp = "{"
            for s,i in best_prices.items():
                resp += str(s) + ":" + str(i["Price"]) + "," + '{:.0f}'.format(i["Time"]) + ";"
            resp = resp[:-1] + "}"
            client_queues[c][0].put(resp)
            t6 = time_ns()
            # print(t5-t1, flush=True)
        print(t3-t2, t4-t3, t5-t4, t6-t5)
    serverObj = {s:serverObj[s] for s in serverObj if len(serverObj[s]) > 0}

    [server_queues.pop(i) for i in rem_list_server]
    [client_queues.pop(i) for i in rem_list_client]
    
    rem_list_client.clear()
    rem_list_server.clear()
    time_i += 1
