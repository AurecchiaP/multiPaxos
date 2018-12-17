# multiPaxos

This is an implementation of multiPaxos, which uses atomic multicast and multiple instances of Paxos to reach decisions on some values proposed by clients.
the implementation is written with Python version 3. The application is multi-threaded to avoid blocking situations.

## Overview

There are 4 types of nodes: Proposers, Acceptors, Clients and Learners. To have a working example it is required to have at least Proposer, Client and Learner, and 2 Acceptors.
The implementation assumes that there are 3 Acceptors, Therefore even when one goes down we would still be able to reach a majority and decide on the values of the clients.

The main flow of the application is as follows: when the nodes are running, a Client can send a message to the group of Proposers; the leader of the Proposers will start a 
new Paxos instance for this message, sending a 1A message to the acceptors and then keep exchanging messages with them until a decision is eventually reached. The decided 
value will then be sent to the learners, which will print the decided values in the order of the paxos instances (which is also the order in which the Proposers receive messages from the Clients).

The Proposers elect a leader by exchanging messages in their own group to let the other Proposers that we are still alive and running; each Proposer then keeps as leader the 
Proposer from which we have received a ping from recently and that has the lowest id. By default a ping is sent every 2 seconds, and after 5 seconds we suspect a Proposer to be down.

There is also a catchup system for both Learners and Proposers: when a Learner notices that it hasn't received a decision for a previous Paxos instance, it will ask the Proposers to 
resend him the missing decision. Also, when a new Proposer appears and it becomes the new leader, it will first catchup the values of the past Paxos instances before starting his 
own new Paxos instances.

## How to test it

For each Node type (Proposer, Acceptor, Learner, Client) there is a .sh script provided to start it; from the root of the project, where the .sh files are located, one can write:

---
    <node script> <id> <path to config file>
---

For example, if we want to start a proposer with id=0 we would do:

---
    ./proposer.sh 0 paxos.conf
---

Where the config file are the IP/port configurations. Note that the path is the absolute path to the file.

## Tests run

I ran all the tests provided, which can be found in the folder paxos-tests (with instruction inside of how to run them). 
I ran all the tests except the ones with message loss locally, with 100 and 1000 values; they all pass, though if attempted with numbers bigger than 1000 they will most likely fail as there is not enough time 
and because the OS buffer for the messages gets overfilled too fast (this is really only an issue when we have all the nodes on a single machine; in this case, sending the messages at a lower rate helps).
I then also ran the tests for message loss on a Ubuntu machine, and the results seem correct. The values sent by the Clients and the ones learned by the Learners will almost always be different, because:

1) The messages from Clients to Proposers can be lost, which means that the Proposers might never know about some values
2) A learner might never know he's missing a value if the missing value is the most recent one

Apart from the tests provided, I also manually ran some tests to make sure that the leader election, Proposer Catchup and learner catchup work as expected.