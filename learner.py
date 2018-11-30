import socket
import struct
import sys
import pickle


from node import Node


class Learner(Node):
    def __init__(self, _id):
        super().__init__('learners')
        self.id = _id
        self.leader = self.id
        self.received_decisions = {}

    def stay_alive(self):
        while True:
            data, addr = self.recv()
            msg = pickle.loads(data)
            if msg.msg_type == "2B":
                # fixme not ballot, but instance (of paxos)
                if msg.ballot not in self.received_decisions:
                    self.received_decisions[msg.ballot] = msg.v_val
                    print(msg.v_val)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the learners")
        sys.exit()
    learner = Learner(sys.argv[1])
    learner.stay_alive()
