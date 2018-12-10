import sys

from node import Node
from message import Message


class Acceptor(Node):
    def __init__(self, _id):
        super().__init__('acceptors')
        self.id = _id        # id of the acceptor
        self.instances = {}  # set of Paxos instances, with {instance_number : state}

    # function that receives messages from the proposers and replies following the Paxos rules
    def receiver_loop(self):
        while True:
            instance, message = self.receive()
            # print("\n================= received message =================")
            # print('instance= ' + str(instance) + "\n" + message.to_string())
            # upon receive 1A
            if message.msg_type == "1A":
                if instance not in self.instances:
                    self.instances[instance] = Message()
                state = self.instances[instance]
                # if the ballot received is higher than the highest one I've participated in
                if message.ballot > state.ballot:
                    # update local state
                    state.ballot = message.ballot
                    # send reply 1B to the proposers
                    reply = Message(msg_type="1B",
                                    leader=message.leader,
                                    ballot=state.ballot,
                                    v_rnd=state.v_rnd,
                                    v_val=state.v_val)
                    self.send((instance, reply), "proposers")
                self.instances[instance] = state

            # upon receive 2A
            elif message.msg_type == "2A":
                # if we hadn't previously received a 1A for this instance, do nothing
                if instance not in self.instances:
                    continue

                # update our current state, and if the round is higher than the previous one, send a 2B reply
                state = self.instances[instance]
                if message.c_rnd >= state.ballot:
                    state.v_rnd = message.c_rnd
                    state.v_val = message.c_val
                    reply = Message(msg_type="2B",
                                    leader=message.leader,
                                    ballot=state.ballot,
                                    v_rnd=state.v_rnd,
                                    v_val=state.v_val)
                    self.send((instance, reply), "proposers")
                self.instances[instance] = state


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the acceptors")
        sys.exit()
    acceptor = Acceptor(sys.argv[1])
    acceptor.receiver_loop()
