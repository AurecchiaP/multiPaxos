import sys
import pickle


from node import Node
from message import Message


class Proposer(Node):
    def __init__(self, _id):
        super().__init__('proposers')
        self.id = _id
        self.instance = 0
        self.instances = {}
        self.ballot = 0
        self.leader = self.id
        self.val = {}
        self.received_1B_count = {}
        self.largest_v_rnd = {}

    def stay_alive(self):
        while True:
            data, addr = self.recv()
            inst, msg = pickle.loads(data)
            print(msg.to_string())
            if msg.msg_type == "0":
                # update state
                self.ballot += 1
                self.val[self.instance] = msg.v_val
                self.received_1B_count[self.instance] = 0
                self.largest_v_rnd[self.instance] = 0
                message = Message("1A", self.ballot, None, None, None, None)
                self.instances[self.instance] = message
                self.send((self.instance, message), "acceptors")
                self.instance += 1

            elif msg.msg_type == "1B":
                print("received 1B")
                print(msg.to_string())
                # check if the ballot of this message is the correct one
                state = self.instances[inst]
                if msg.ballot == state.ballot:
                    print(self.received_1B_count)
                    self.received_1B_count[inst] += 1
                    if msg.v_rnd > self.largest_v_rnd[inst]:
                        self.largest_v_rnd[inst] = msg.v_rnd
                    if self.received_1B_count[inst] > 1:
                        print("quorum reached")
                        print(self.val)
                        if self.largest_v_rnd[inst] != 0:
                            state.c_val = msg.v_val
                        else:
                            state.c_val = self.val[inst]
                        message = Message("2A", state.ballot, None, None, state.ballot, state.c_val)
                        self.send((inst, message), "acceptors")
                self.instances[inst] = state


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the proposer")
        sys.exit()
    proposer = Proposer(sys.argv[1])
    proposer.stay_alive()
