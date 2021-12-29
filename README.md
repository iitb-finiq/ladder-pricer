# Ladder Pricer
## Problem Statement:

**PART 1**: Create a new model for pricing in which the banks(from here off denoted as suppliers) only send the prices/size for different "slabs" and the FINIQ server is responsible for getting the best price for the requested size.
E.g.: Suppose the bank gives the following slabs:
| Size | Price per size |
|------|-------|
| 1M | 1.033 |
| 5M | 1.032 |
| 10M | 1.034 |

For the request of 11M, the best possible price is 11.353 (Buy 2 5M and 1 1M).

**PART 2:** Using the above code as baseline, create a full supplier-client multi-threaded system which simulates the real life scenerio. Also load test the program with multiple suppliers and clients.

## Part 1: Idea
The code is based on basic dynamic programming. The following defines the variable: $dp(i)$ denotes the best price for $size = i$.

Notice that for each of the size, there would be only one order corresponding to its size or there would be atleast 2 orders. The first case can be handled by initialising $dp(i)$ to be the price of its slab. For the second case, we iterate over the size of 1 order and find the minimum price possible. So,
$$
    dp(i) = min_{j=0 \cdots i} \{j*dp(j) + (i-j)*dp(i-j)\}
$$
The code for this is written in `BidPricer.java`. It has 1 function named `parsefix` which is responsible for parsing the fix and extracting the slabs and corresponding prices. It also initialises the `dp` array.

The second function names `getBestPrice` is responsible for the above iteration and calculates the best price ($dp(i)$) for the request $i$ given in parameter.
## Directory Structure
The folder contains 2 folders: `java` and `python` depending on the language in which the middle server code is written. Each of them have `server.py` and `client.py` which are the codes for creating (multiple) suppliers and clients. 

The file `BidPricer.java` contains the code for ladder pricing i.e. given a fix and a request, return the corresponding price.

Finally, `middle.java` / `middle.py` contains the code that is used to create the middle server which is responsible for taking fixes from supplier and process the requests by client. It is a multi-threaded code in which each fix as well as request is processed in a different thread.

## Running instructions
 1. First create a package from `BidPricer.java`. To do this, run the following command:
    > java -d . BidPricer.java 
 2. Set the hyper-parameters in `server.py` and `client.py` file. This includes `num_servers`, `gap_btw_fixes` and `valid_period` in  `server.py` and `num_clients` in `client.py`. Also change the number of fixes and requests in the for loop.
 3. Run the middle server. 
    > For the python file, run: `python middle.py`

    > For the java file, run: `javac middle.java; java middle`'
 4. Run `server.py` and `client.py` simultaneously. They can be run from different terminals or one of them can be run in the background. 
    > To run in different terminal, run `python server.py` and `python client.py` in two terminals.

    > To run in the same terminal, execute `python server.py & python client.py`.


