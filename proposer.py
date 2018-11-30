import socket
import struct
import sys
import pickle


from node import Node
from message import Message

# TODO leader cose
class Proposer(Node):
    def __init__(self, _id):
        super().__init__('proposers')
        self.id = _id
        self.ballot = 0
        self.leader = self.id
        self.val = None
        self.received_1B_count = 0
        self.largest_v_rnd = 0

    def stay_alive(self):
        while True:
            data, addr = self.recv()
            msg = pickle.loads(data)
            print(msg.to_string())
            if msg.msg_type == "0":
                # update state
                self.ballot += 1
                self.val = msg.v_val
                self.received_1B_count = 0
                message = Message("1A", self.ballot, None, None, None, None)
                self.send(message, "acceptors")

            elif msg.msg_type == "1B":
                print("received 1B")
                print(msg.to_string())
                # check if the ballot of this message is the correct one
                if msg.ballot == self.ballot:
                    self.received_1B_count += 1
                    if msg.v_rnd > self.largest_v_rnd:
                        self.largest_v_rnd = msg.v_rnd
                    if self.received_1B_count > 1:
                        print("quorum reached")
                        if self.largest_v_rnd != 0:
                            self.val = msg.v_val
                        message = Message("2A", self.ballot, None, None, self.ballot, self.val)
                        self.send(message, "acceptors")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the proposer")
        sys.exit()
    proposer = Proposer(sys.argv[1])
    proposer.stay_alive()
