import sys
import pickle

from node import Node


class Learner(Node):
    def __init__(self, _id):
        super().__init__('learners')
        self.id = _id                   # id of learner
        self.received_decisions = {}    # dict of {paxos_instance : decision}

    def stay_alive(self):
        while True:
            data, address = self.receive()
            instance, message = pickle.loads(data)
            if message.msg_type == "2B":
                if instance not in self.received_decisions:
                    self.received_decisions[instance] = message.v_val
                    print(message.v_val)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the learners")
        sys.exit()
    learner = Learner(sys.argv[1])
    learner.stay_alive()
