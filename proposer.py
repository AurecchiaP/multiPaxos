import sys
import pickle
import threading
import time

from node import Node
from message import Message


class Proposer(Node):
    def __init__(self, _id):
        super().__init__('proposers')
        self.id = _id                # id of the proposer
        self.instance = 0            # number of most recent Paxos instance
        self.instances_decided = {}  # dict {paxos_instance : decided} keeps track of which instances have been decided
        self.instances = {}          # dict {paxos_instance : state} stores the Paxos state for each instance
        self.leader = self.id        # current leader
        self.val = {}                # dict {paxos_instance : v} that stores the proposed value for Paxos inst
        self.received_1B_count = {}  # dict {paxos_instance : v} that stores the number of msg received for Paxos inst
        self.largest_v_rnd = {}      # dict {paxos_instance : v} that stores the largest v_rnd received for Paxos inst
        self.proposers_pings = {}    # dict {proposer_id : time} that stores when we received the last ping from them
        self.instances_start_time = {}  # dict {instance : time} that stores when we started this instance

        # create the two threads for the timeout of messages and the leader election messages
        self.timeout_thread = threading.Thread(target=self.message_timeout, name="timeout_thread", daemon=True)
        self.election_thread = threading.Thread(target=self.leader_election, name="election_thread", daemon=True)

    def receiver_loop(self):
        self.election_thread.start()
        while True:
            data, address = self.receive()
            instance, message = pickle.loads(data)
            print("\n================= received message =================")
            print('instance= ' + str(instance) + "\n" + message.to_string())
            if message.msg_type == "ELECTION":
                self.proposers_pings[message.id] = time.time()
                # if we received a ping from someone with a lower id, he's the leader
                if message.leader < self.leader:
                    self.leader = message.leader
                    print("new leader: " + str(self.leader))
                # if we haven't heard from the leader in a while, elect a new leader
                if time.time() - self.proposers_pings[self.leader] > 20:
                    del self.proposers_pings[self.leader]
                    self.leader = sorted(self.proposers_pings.keys())[0]
                    print("new leader: " + str(self.leader))

            elif message.msg_type == "CATCHUP":
                print(self.instances)
                new_message = Message(msg_type="2B", v_val=self.instances_decided[instance])
                # new_message = Message(msg_type="2B", v_val=self.instances[instance].v_val)
                self.send((instance, new_message), "learners")

            # we handle the message if it type 0(a message from a client) or if we are the current leader
            if message.msg_type == "0" or message.msg_type == "2B" or message.leader == self.leader:
                if message.msg_type == "0":
                    self.instances[self.instance] = message
                    state = self.instances[self.instance]
                    # update state
                    # FIXME when do I update the ballot? it's for the same paxos instance
                    state.ballot += 10
                    self.val[self.instance] = message.v_val
                    self.received_1B_count[self.instance] = 0
                    self.largest_v_rnd[self.instance] = 0
                    new_message = Message(msg_type="1A", ballot=state.ballot, leader=self.leader)
                    self.instances[self.instance] = state
                    self.send((self.instance, new_message), "acceptors")
                    self.instance += 1

                elif message.msg_type == "1B":
                    # check if the ballot of this message is the correct one
                    state = self.instances[instance]
                    if message.ballot == state.ballot:
                        self.received_1B_count[instance] += 1
                        if message.v_rnd > self.largest_v_rnd[instance]:
                            self.largest_v_rnd[instance] = message.v_rnd
                        if self.received_1B_count[instance] > 1:
                            # FIXME this sends more than one 2A since we reach more quorums
                            print("quorum reached")
                            if self.largest_v_rnd[instance] != 0:
                                state.c_val = message.v_val
                            else:
                                state.c_val = self.val[instance]
                            new_message = Message(msg_type="2A",
                                                  ballot=state.ballot,
                                                  leader=self.leader,
                                                  c_rnd=state.ballot,
                                                  c_val=state.c_val)
                            self.send((instance, new_message), "acceptors")
                    self.instances[instance] = state

                elif message.msg_type == "2B":
                    # fixme check for majority?
                    self.instances_decided[instance] = message.v_val

    def leader_election(self):
        while True:
            message = Message(msg_type="ELECTION", leader=self.leader, id=self.id)
            self.send((self.instance, message), "proposers")
            time.sleep(10)

    def message_timeout(self):
        # todo check if this works
        while True:
            if self.leader == self.id:
                for instance, start_time in self.instances_start_time.items():
                    if instance not in self.instances_decided and time.time() - start_time > 10:
                        state = self.instances[instance]
                        state.ballot += 10
                        if state.msg_type == "1B" and self.received_1B_count[instance] > 1:
                            # we had reached a quorum; resend 2A
                            new_message = Message(msg_type="2A",
                                                  ballot=state.ballot,
                                                  leader=self.leader,
                                                  c_rnd=state.ballot,
                                                  c_val=state.c_val)
                            self.send((instance, new_message), "acceptors")

                        else:
                            # we didn't reach a quorum; resend 1A
                            self.received_1B_count[instance] = 0
                            new_message = Message(msg_type="1A", ballot=state.ballot, leader=self.leader)
                            self.instances[self.instance] = state
                            self.send((self.instance, new_message), "acceptors")
            time.sleep(10)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the proposer")
        sys.exit()
    proposer = Proposer(sys.argv[1])
    proposer.receiver_loop()
