import sys

from node import Node
from message import Message
import time


class Learner(Node):
    def __init__(self, _id):
        super().__init__('learners')
        self.id = _id                   # id of learner
        self.last_delivered = -1        # counter of the last printed decision
        self.max_instance = -1          # counter of the last printed decision
        self.received_decisions = {}    # dict of {paxos_instance : decision}
        self.timeout = 0

    def receiver_loop(self):
        while True:
            # receive a message
            instance, message = self.receive()
            # if it is a decision message (2B)
            if message.msg_type == "DECISION":
                # if this instance is the greatest one we have seen so far, update the max_instance
                if instance > self.max_instance:
                    self.max_instance = instance
                # if we haven't seen this instance before, save its value
                if instance not in self.received_decisions:
                    self.received_decisions[instance] = message.v_val
                # if we can deliver/print the next message in order, do so and update the learner's state
                while self.last_delivered < self.max_instance and self.last_delivered + 1 in self.received_decisions:
                    self.last_delivered += 1
                    print(self.received_decisions[self.last_delivered], flush=True)
                # check if there are more missing messages
                if time.time() - self.timeout > 2:
                    self.ask_missing_values()
                    self.timeout = time.time()

            # if we received a reply of type CATCHUP
            elif message.msg_type == "CATCHUP_B":
                received_values = message.v_val
                # a catchup message contains a dict of values instead of only one, to make the catchup faster
                for instance, value in received_values.items():
                    if instance not in self.received_decisions:
                        self.received_decisions[instance] = value
                # if we can deliver/print the next message in order, do so and update the learner's state
                while self.last_delivered < self.max_instance and self.last_delivered + 1 in self.received_decisions:
                    self.last_delivered += 1
                    print(self.received_decisions[self.last_delivered], flush=True)
                # check if there are more missing messages
                if time.time() - self.timeout > 2:
                    self.ask_missing_values()
                    self.timeout = time.time()

    def ask_missing_values(self):
        # go through the list of instances from the last printed/delivered one to the maximum one we have received,
        # store the missing ones, and ask them to the proposers in chunks of 20 at a time to avoid having huge messages
        missing_values = []
        for instance in range(self.last_delivered + 1, self.max_instance + 1):
            if instance not in self.received_decisions:
                missing_values.append(instance)

        if len(missing_values) > 0:
            chunks = [missing_values[x:x + 20] for x in range(0, len(missing_values), 20)]
            for chunk in chunks:
                new_message = Message(msg_type="CATCHUP_A", v_val=chunk)
                self.send((None, new_message), "proposers")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the learners")
        sys.exit()
    learner = Learner(sys.argv[1])
    learner.receiver_loop()
