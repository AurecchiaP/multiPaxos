import sys
import pickle

from node import Node
from message import Message


class Acceptor(Node):
    def __init__(self, _id):
        super().__init__('acceptors')
        self.id = _id        # id of the acceptor
        self.instances = {}  # set of Paxos instances, with {instance_number : state}

    def receiver_loop(self):
        while True:
            data, address = self.receive()
            instance, message = pickle.loads(data)
            # print("\n================= received message =================")
            # print('instance= ' + str(instance) + "\n" + message.to_string())
            # upon receive 1A
            # TODO should I check if message was sent by leader? does the acceptor even know who the leader is?
            if message.msg_type == "1A":
                if instance not in self.instances:
                    self.instances[instance] = Message()
                state = self.instances[instance]
                # if the ballot received is higher than the highest one I've participated in
                if message.ballot > state.ballot:
                    # update local state
                    state.ballot = message.ballot
                    # send reply
                    reply = Message(msg_type="1B",
                                    leader=message.leader,
                                    ballot=state.ballot,
                                    v_rnd=state.v_rnd,
                                    v_val=state.v_val)
                    self.send((instance, reply), "proposers")
                self.instances[instance] = state

            elif message.msg_type == "2A":
                if instance not in self.instances:
                    continue
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
