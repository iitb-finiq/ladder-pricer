import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.*;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.stream.Collectors;
import BidPricer.BidPricer;

class ServerElement{
    public long end_time;
    public LinkedHashMap<String, String> lh;
    public volatile BidPricer bp;
    public boolean thread_joined = false;
    public Thread th;
    
    ServerElement() {
        bp = new BidPricer();
    }

    public Double run(Double notion) {
        if(!thread_joined) {
            try {
                th.join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
            thread_joined = true;    
        }
        Double f = bp.getBestPrice(notion);
        return f;
    }
}

class CompareSE implements Comparator<ServerElement> {
  public int compare(ServerElement a, ServerElement b)
    {
         return (int) (a.end_time - b.end_time);
    }
}
 
class Server_responses {
    public volatile PriorityQueue<ServerElement> fix;
    public Lock lock;
    public Server_responses() {
        lock = new ReentrantLock();
        fix = new PriorityQueue<ServerElement>(new CompareSE());
    }
}

class Client_Response {
    public volatile Double notion;
    public boolean isprocessed = false;
    public volatile Map<String, Double> prices = new TreeMap<String, Double>();
    public volatile Map<String, Long> end_time = new TreeMap<String, Long>();

    public String getData() {
        List<Thread> thread = new ArrayList<>();
        for (Map.Entry<Integer,Server_responses> entry : middle.serverobj.entrySet()) {
            entry.getValue().lock.lock();
            Iterator<ServerElement> it = entry.getValue().fix.iterator();
            while(it.hasNext()) {
                ServerElement s = it.next();
                this.setData(entry.getKey().toString(), s.run(notion), s.end_time);
                // Thread t = new Thread(() -> {this.setData(entry.getKey().toString(), s.run(notion), s.end_time);});
                // t.start();
                // thread.add(t);
            }
        }
        for (Thread t: thread)
            try {
                t.join();
            } catch (InterruptedException e1) {
                e1.printStackTrace();
            }
        for (Map.Entry<Integer,Server_responses> entry : middle.serverobj.entrySet()) {
            entry.getValue().lock.unlock();
        }
        String resp = prices.keySet().stream().map(sr -> sr + ":" + prices.get(sr).toString() + "," + end_time.get(sr).toString()).collect(Collectors.joining(";", "{", "}"));
        prices.clear();
        end_time.clear();
        return resp;
    }

    public void setData(String sr, Double bp, long et) {
        if(et < System.nanoTime()) {
            // System.out.print(et);
            // System.out.print(" ");
            // System.out.println(System.nanoTime());   
            return;
        }
        if(!prices.containsKey(sr)) {
            prices.put(sr, bp);
            end_time.put(sr, et);
        }
        else {
            if( prices.get(sr) < bp || (prices.get(sr) == bp && et > end_time.get(sr)) ) {
                prices.put(sr, bp);
                end_time.put(sr, et);
            }
        }
    }
}

class Server_Thread extends Thread {
    SocketChannel s;
    Server_responses q;
    int id;

    public Server_Thread(SocketChannel _s, Server_responses _q, int _id) {
        s = _s;
        q = _q;
        id = _id;
        try {
            System.out.println("sending");
            s.write(ByteBuffer.wrap("started".getBytes()));
            System.out.println("sent");
        } catch (IOException e) {
            System.out.println("error");
            e.printStackTrace();
        }
    }

    @Override
    public void run() {
        String leftover = "";
        while (true) {
            q.lock.lock();
            // System.out.println(q.fix.size());
            while(q.fix.peek() != null && q.fix.peek().end_time < System.nanoTime()) {
                q.fix.poll();
            }
            // System.out.println(q.fix.size());
            q.lock.unlock();
            try {
                String response;
                Map<String, String> resp = new HashMap<String,String>();
                do {
                    ByteBuffer dst = ByteBuffer.allocate(8192);
                    if(s.read(dst) < 0) return;
                    leftover = leftover.concat(new String(dst.array()).toLowerCase().trim()).trim();
                    String[] sp = leftover.split("###", 2);
                    if(sp.length < 2) {
                        continue;
                    }
                    else {
                        response = sp[0];
                        leftover = sp[1];
                        if (response.equals("end")) {
                            s.close();
                            System.out.println("server " + Integer.toString(id) + "closing");
                            while(q.fix.size()!=0) {
                                while(q.fix.peek() != null && q.fix.peek().end_time < System.nanoTime()) {
                                    q.fix.poll();
                                }
                            }
                            return;
                        }
                        resp =  Arrays.asList(response.split(";")).stream().map((x) -> x.split(":", 2)).collect(Collectors.toMap((x) -> x[0], (x) -> x[1]));
                    } 
                } while (!resp.containsKey("fix"));
                ServerElement se = new ServerElement();
                Long start_time = System.nanoTime();
                if(resp.containsKey("start_time")) {
                    start_time = Long.parseLong(resp.get("start_time").trim());
                }
                se.end_time = start_time + Long.parseLong(resp.getOrDefault("ttl", middle.valid_period));
                if(se.end_time <= System.nanoTime()) continue;
                se.lh = new LinkedHashMap<>(resp);
                se.th = new Thread(() -> {se.bp.parseFix(se.lh.get("fix"));});
                se.th.start();
                q.lock.lock();
                q.fix.add(se);
                q.lock.unlock();
            } catch (IOException e) {
                e.printStackTrace();
            }
            // catch (ArrayIndexOutOfBoundsException e) {
            //     try {
            //         s.close();
            //     } catch (IOException e1) {
            //         e1.printStackTrace();
            //     }
            //     System.out.println("server " + Integer.toString(id) + "closing");
            //     while(q.fix.size()!=0) {
            //         while(q.fix.peek() != null && q.fix.peek().end_time < System.nanoTime()) {
            //             q.fix.poll();
            //         }
            //     }
            //     return;
            // }
        }
    }
}

class Client_Thread extends Thread {
    SocketChannel s;
    Client_Response q;
    int id;

    public Client_Thread(SocketChannel _s, Client_Response _q, int _id) {
        s = _s;
        q = _q;
        id = _id;
        try {
            s.write(ByteBuffer.wrap("started".getBytes()));
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void run() {
        while (true) {
            try {
                String response;
                Map<String, String> resp;
                do {
                    ByteBuffer dst = ByteBuffer.allocate(8192);
                    if(s.read(dst) < 0) return;
                    dst.flip();
                    response = new String(dst.array()).toLowerCase().trim();
                    if (response.equals("end")) {
                        s.close();
                        System.out.println("client " + Integer.toString(id) + "closing");
                        return;
                    }
                    resp = Arrays.asList(response.split(";")).stream().map((x) -> x.split(":", 2))
                            .collect(Collectors.toMap((x) -> x[0], (x) -> x[1]));
                } while (!resp.containsKey("notional"));

                q.notion = Double.parseDouble(resp.get("notional"));
                s.write(ByteBuffer.wrap(q.getData().getBytes()));
            } catch (IOException e) {
                e.printStackTrace();
            }
            catch (ArrayIndexOutOfBoundsException e) {
                try {
                    s.close();
                } catch (IOException e1) {
                    e1.printStackTrace();
                }
                System.out.println("client " + Integer.toString(id) + "closing");
                return;
            }
        }
    }
}

public class middle {
    static public String valid_period = "0.2";
    static public double new_request_timeout = 0;
    static private int server_socket = 3456;
    static private int client_socket = 2345;
    static public volatile Map<Integer, Server_responses> serverobj = new LinkedHashMap<Integer, Server_responses>();
    public static void main(String[] args) {
        try {
            ServerSocketChannel ss = ServerSocketChannel.open();
            ServerSocketChannel mss = ServerSocketChannel.open();
            ss.configureBlocking(false);
            mss.configureBlocking(false);
            ss.bind(new InetSocketAddress(client_socket));
            mss.bind(new InetSocketAddress(server_socket));
            int serverID = 0;
            int clientID = 0;
            System.out.println("Sockets created");
            while (true) {
                SocketChannel s = ss.accept();// establishes connection
                if(s != null) {
                    Client_Response cr = new Client_Response();
                    Client_Thread st = new Client_Thread(s, cr, clientID);
                    st.start();
                    clientID++;
                }
                SocketChannel ms = mss.accept();// establishes connection
                if(ms != null) {
                    Server_responses sr = new Server_responses();
                    serverobj.put(serverID, sr);
                    System.out.println("response object created");
                    Server_Thread st = new Server_Thread(ms, sr,serverID);
                    st.start();
                    serverID++;
                }
            }
        } catch (Exception e) {
            System.out.println(e);
        }
    }
}