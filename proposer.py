import sys
import threading
import time
import queue

from node import Node
from message import Message

lock = threading.Lock()


class Proposer(Node):
    def __init__(self, _id, config_path):
        super().__init__('proposers', config_path)
        # Proposer's basic state
        self.id = _id                       # id of the proposer
        self.leader = self.id               # current leader, initialised to myself
        self.client_values = queue.Queue()  # queue of the values received from the clients
        self.message_queue = queue.Queue()  # queue of the messages received

        # information on the various Paxos instances
        self.instance = 0            # number of most recent Paxos instance
        self.instances_decided = {}  # dict {Paxos_instance : decision} keeps track of which instances have been decided
        self.instances = {}          # dict {Paxos_instance : state} stores the Paxos state(a Message) for each instance
        self.received_1B_count = {}  # dict {Paxos_instance : val} that stores the number of msg received for Paxos inst
        self.received_2B_count = {}  # dict {Paxos_instance : val} that stores the number of msg received for Paxos inst
        self.largest_v_rnd = {}      # dict {Paxos_instance : val} that stores the largest v_rnd received for Paxos inst

        # information used for leader election and timeout of messages
        self.proposers_pings = {}       # dict {proposer_id : time} that stores when we received the last ping from them
        self.instances_start_time = {}  # dict {instance : time} that stores when we started this instance

        # create 3 threads: one handles the messages received, one handles the timeout of messages, one the election
        self.handler_thread = threading.Thread(target=self.message_handler, name="handler_thread", daemon=True)
        self.timeout_thread = threading.Thread(target=self.message_timeout, name="timeout_thread", daemon=True)
        self.election_thread = threading.Thread(target=self.leader_election, name="election_thread", daemon=True)

    # function that continuously gets the received messages from the socket and puts them in a queue
    def receiver_loop(self):
        self.handler_thread.start()
        self.election_thread.start()
        self.timeout_thread.start()
        while True:
            instance, message = self.receive()
            self.message_queue.put((instance, message))

    # function that pops the received messages from a queue and handles them depending on their type; they can be of
    # type ELECTION (for leader election), type CATCHUP_A (a request from a learner to resend previous decisions),
    # type 0 (a message from a client for a value to be proposed), and 1B and 2B for Paxos
    def message_handler(self):
        while True:
            if self.message_queue.empty():
                continue
            instance, message = self.message_queue.get()

            # handle an ELECTION message received by other proposers
            if message.msg_type == "ELECTION":
                # save the time we received this message, so that we know that the proposer that sent it is alive
                self.proposers_pings[message.id] = time.time()
                # if we received a ping from someone with a lower id, he's the new leader
                if message.id < self.leader:
                    self.leader = message.id
                # if we haven't heard from the leader in a while, elect a new leader (the next one with lowest id)
                if self.leader != self.id and time.time() - self.proposers_pings[self.leader] > 5:
                    del self.proposers_pings[self.leader]
                    self.leader = sorted(self.proposers_pings.keys())[0]

            # handle a CATCHUP request from a learner; the reply to the learner will be a dictionary {instance : value}
            # of the values he's missing
            elif message.msg_type == "CATCHUP_A":
                values = message.v_val
                reply_values = {}
                for instance in range(len(values)):
                    # if we (the proposer) know about the previous decision, add the value to the reply
                    if values[instance] in self.instances_decided:
                        reply_values[values[instance]] = self.instances_decided[values[instance]]
                # send the catchup reply to the learners
                new_message = Message(msg_type="CATCHUP_B", v_val=reply_values)
                self.send((instance, new_message), "learners")

            # if it's a message of type 0 (meaning a message from client to proposer) and we are the current leader
            elif message.msg_type == "0" and self.leader == self.id:
                # self.client_values[self.instance] = message.v_val
                self.client_values.put(message.v_val)
                self.instances[self.instance] = message
                state = self.instances[self.instance]
                # initialize the state for this instance
                state.ballot += 10
                self.received_1B_count[self.instance] = 0
                self.received_2B_count[self.instance] = 0
                self.largest_v_rnd[self.instance] = 0
                # send 1A to acceptors
                new_message = Message(msg_type="1A", ballot=state.ballot, leader=self.leader)
                self.instances[self.instance] = state
                self.send((self.instance, new_message), "acceptors")
                # save the current time that we can use for the timeout when we don't receive a reply
                with lock:
                    self.instances_start_time[self.instance] = time.time()
                self.instance += 1

            # if it's a message of type 1B and it was meant for us and we are the current leader
            elif message.msg_type == "1B" and message.leader == self.leader and self.leader == self.id:
                # check if the ballot of this message is the correct one
                if instance not in self.instances:
                    self.instances[instance] = Message()
                # load the state for this instance
                state = self.instances[instance]
                # if the ballot of the message is the right one
                if message.ballot == state.ballot:
                    # increase the counter of 1B received for this ballot
                    self.received_1B_count[instance] += 1
                    # store the highest v_rnd received
                    if message.v_rnd > self.largest_v_rnd[instance]:
                        self.largest_v_rnd[instance] = message.v_rnd
                    # if we have received a majority of 1B (2 or more since we have 3 acceptors)
                    if self.received_1B_count[instance] == 2:
                        # choose the value to propose (one received from an acceptor or one received from a client)
                        if self.largest_v_rnd[instance] != 0:
                            state.c_val = message.v_val
                            # if this Paxos instance was already bound to a value, start a new 1A (Paxos instance)
                            self.re_send_1A()
                            self.instances_decided[instance] = state.c_val
                            # send the 2A
                            new_message = Message(msg_type="2A",
                                                  ballot=state.ballot,
                                                  leader=self.leader,
                                                  c_rnd=state.ballot,
                                                  c_val=state.c_val)
                            self.send((instance, new_message), "acceptors")
                        else:
                            if not self.client_values.empty():
                                state.c_val = self.client_values.get()
                                # send the 2A
                                new_message = Message(msg_type="2A",
                                                      ballot=state.ballot,
                                                      leader=self.leader,
                                                      c_rnd=state.ballot,
                                                      c_val=state.c_val)
                                self.send((instance, new_message), "acceptors")
                # update our state for this instance
                with lock:
                    self.instances_start_time[instance] = time.time()
                self.instances[instance] = state

            # if the message is 2B
            elif message.msg_type == "2B" and message.leader == self.leader and self.leader == self.id:
                # load the state
                state = self.instances[instance]
                # if it is the right ballot
                if message.ballot >= state.ballot:
                    # increase the counter of 2B received for this instance
                    self.received_2B_count[instance] += 1
                    # if we have received a majority of 2B
                    if self.received_2B_count[instance] == 2:
                        # save the value decided and send the decision to the learners
                        self.instances_decided[instance] = message.v_val
                        # delete the timeout for this instance
                        with lock:
                            if instance in self.instances_start_time:
                                del self.instances_start_time[instance]
                        reply = Message(msg_type="DECISION", v_val=message.v_val)
                        self.send((instance, reply), "learners")
                        # self.client_values[instance] = message.v_val

    # function that starts a new Paxos instance; it is called when a proposer had started a Paxos instance with an
    # instance number that had already been used before, and therefore the proposer couldn't propose its own value
    def re_send_1A(self):
        self.instances[self.instance] = Message()
        state = self.instances[self.instance]
        # initialize the state for this instance
        state.ballot += 10
        self.received_1B_count[self.instance] = 0
        self.received_2B_count[self.instance] = 0
        self.largest_v_rnd[self.instance] = 0
        # send 1A to acceptors
        new_message = Message(msg_type="1A", ballot=state.ballot, leader=self.leader)
        self.instances[self.instance] = state
        self.send((self.instance, new_message), "acceptors")
        # save the current time that we can use for the timeout when we don't receive a reply
        with lock:
            self.instances_start_time[self.instance] = time.time()
        self.instance += 1

    # function for leader election; every 2 seconds it sends a message to other proposers to find out who the leader is
    def leader_election(self):
        while True:
            message = Message(msg_type="ELECTION", leader=self.leader, id=self.id)
            self.send((self.instance, message), "proposers")
            time.sleep(2)

    # handles the timeout of messages
    def message_timeout(self):
        while True:
            if self.leader == self.id:
                with lock:
                    # for every sent message, if we didn't receive a reply in a while, update the ballot and resend it
                    for instance, start_time in self.instances_start_time.items():
                        # if the instance hadn't be already decided and it timed out
                        if instance not in self.instances_decided and time.time() - start_time > 5:
                            state = self.instances[instance]
                            state.ballot += 100
                            # if we had a majority of 1B already, resend only 2A
                            if state.msg_type == "1B" and self.received_1B_count[instance] > 1:
                                new_message = Message(msg_type="2A",
                                                      ballot=state.ballot,
                                                      leader=self.leader,
                                                      c_rnd=state.ballot,
                                                      c_val=state.c_val)
                                self.send((instance, new_message), "acceptors")
                            # resend 1A
                            else:
                                self.received_1B_count[instance] = 0
                                new_message = Message(msg_type="1A", ballot=state.ballot, leader=self.leader)
                                self.instances[instance] = state
                                self.send((instance, new_message), "acceptors")
                            self.instances[instance] = state
            time.sleep(2)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("give the id of the proposer and the config_path")
        sys.exit()
    proposer = Proposer(sys.argv[1], sys.argv[2])
    proposer.receiver_loop()
