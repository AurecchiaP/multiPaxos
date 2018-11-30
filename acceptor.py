import sys
import pickle

from node import Node
from message import Message


class Acceptor(Node):
    def __init__(self, _id):
        super().__init__('acceptors')
        self.id = _id
        self.leader = self.id
        self.instances = {}
        self.ballot = 0  # highest round participated in
        self.v_rnd = 0
        self.v_val = None

    def stay_alive(self):
        while True:
            data, addr = self.recv()
            inst, msg = pickle.loads(data)
            print(msg.to_string())
            # upon receive 1A
            # TODO should I check if message was sent by leader? does the acceptor even know who the leader is?
            if msg.msg_type == "1A":
                print("received 1A")
                print('inst ' + str(inst))
                if inst not in self.instances:
                    self.instances[inst] = Message(None, 0, 0, None, 0, None)
                state = self.instances[inst]
                # if the ballot received is higher than the highest one I've participated in
                if msg.ballot > state.ballot:
                    # update local state
                    state.ballot = msg.ballot
                    # send reply
                    reply = Message("1B", state.ballot, state.v_rnd, state.v_val, None, None)
                    self.send((inst, reply), "proposers")
                    print("sent")
                self.instances[inst] = state

            elif msg.msg_type == "2A":
                print("received 2A")
                if inst not in self.instances:
                    continue  # TODO makes sense?
                state = self.instances[inst]
                if msg.c_rnd >= state.ballot:
                    state.v_rnd = msg.c_rnd
                    state.v_val = msg.c_val
                    reply = Message("2B", state.ballot, state.v_rnd, state.v_val, None, None)
                    self.send((inst, reply), "learners")
                self.instances[inst] = state


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the acceptors")
        sys.exit()
    acceptor = Acceptor(sys.argv[1])
    acceptor.stay_alive()
