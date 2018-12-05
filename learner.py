import sys
import pickle

from node import Node
from message import Message


# FIXME a newly instantiated learner only sends catchup after receiving a message; might want to catchup before that
class Learner(Node):
    def __init__(self, _id):
        super().__init__('learners')
        self.id = _id                   # id of learner
        self.last_delivered = -1        # counter of the last printed decision
        self.max_instance = -1          # counter of the last printed decision
        self.received_decisions = {}    # dict of {paxos_instance : decision}

    def receiver_loop(self):
        while True:
            # receive a message
            data, address = self.receive()
            instance, message = pickle.loads(data)
            # if it is a decision message (2B)
            if message.msg_type == "2B":
                # if this instance is the greatest one we have seen so far, update the max_instance
                if instance > self.max_instance:
                    self.max_instance = instance
                # if we haven't seen this instance before, save its value
                if instance not in self.received_decisions:
                    self.received_decisions[instance] = message.v_val
                # if we can deliver/print the next message in order, do so and update the learner's state
                # TODO check if works
                while self.last_delivered < self.max_instance and self.last_delivered + 1 in self.received_decisions:
                    self.last_delivered += 1
                    print(self.received_decisions[self.last_delivered], flush=True)
                if self.last_delivered < self.max_instance:
                    new_message = Message(msg_type="CATCHUP")
                    self.send((self.last_delivered + 1, new_message), "proposers")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the learners")
        sys.exit()
    learner = Learner(sys.argv[1])
    learner.receiver_loop()
