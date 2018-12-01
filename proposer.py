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
        self.instances = {}          # dict {paxos_instance : state} stores the Paxos state for each instance
        self.leader = self.id        # current leader
        self.val = {}                # dict {paxos_instance : v} that stores the proposed value for Paxos inst
        self.received_1B_count = {}  # dict {paxos_instance : v} that stores the number of msg received for Paxos inst
        self.largest_v_rnd = {}      # dict {paxos_instance : v} that stores the largest v_rnd received for Paxos inst
        self.proposers_pings = {}    # dict {proposer_id : time} that stores when we received the last ping from them

    def stay_alive(self):
        threading.Thread(target=self.leader_election, name="election_thread", daemon=True).start()
        while True:
            data, address = self.receive()
            instance, message = pickle.loads(data)
            print("\n================= received message =================")
            print('instance= ' + str(instance) + "\n" + message.to_string())
            if message.msg_type == "ELECTION":
                self.proposers_pings[message.v_val] = time.time()
                # if we have more candidate leaders and the last received message from leader was more than 20s ago
                if len(self.proposers_pings) > 1 and self.proposers_pings[self.leader] - time.time() > 20:
                    # possibly the same leader, but still lowest id
                    del self.proposers_pings[self.leader]
                    self.leader = sorted(self.proposers_pings.keys())[0]
                    print("new leader: " + str(self.leader))

            # if we are the leader, then handle the message
            if message.msg_type == "0" or message.leader == self.leader:
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
                            self.received_1B_count[instance] = 0  # FIXME HACK
                            print("quorum reached")
                            if self.largest_v_rnd[instance] != 0:
                                state.c_val = message.v_val
                            else:
                                state.c_val = self.val[instance]
                            new_message = Message(msg_type="2A", ballot=state.ballot, c_rnd=state.ballot, c_val=state.c_val)
                            self.send((instance, new_message), "acceptors")
                    self.instances[instance] = state

    def leader_election(self):
        while True:
            message = Message(msg_type="ELECTION", id=self.id)
            self.send((self.instance, message), "proposers")
            time.sleep(10)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the proposer")
        sys.exit()
    proposer = Proposer(sys.argv[1])
    proposer.stay_alive()
