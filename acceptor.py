import socket
import struct
import sys
import pickle


from node import Node
from message import Message


class Acceptor(Node):
    def __init__(self, _id):
        super().__init__('acceptors')
        self.id = _id
        self.leader = self.id
        self.ballot = 0  # highest round participated in
        self.v_rnd = 0
        self.v_val = None

    def stay_alive(self):
        while True:
            data, addr = self.recv()
            msg = pickle.loads(data)
            print(msg.to_string())
            # upon receive 1A
            # TODO should I check if message was sent by leader? does the acceptor even know who the leader is?
            if msg.msg_type == "1A":
                print("received 1A")
                # if the ballot received is higher than the highest one I've participated in
                if msg.ballot > self.ballot:
                    # update local state
                    self.ballot = msg.ballot
                    # send reply
                    reply = Message("1B", self.ballot, self.v_rnd, self.v_val, None, None)
                    self.send(reply, "proposers")

            elif msg.msg_type == "2A":
                print("received 2A")
                if msg.c_rnd >= self.ballot:
                    self.v_rnd = msg.c_rnd
                    self.v_val = msg.c_val
                    reply = Message("2B", self.ballot, self.v_rnd, self.v_val, None, None)
                    self.send(reply, "learners")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the acceptors")
        sys.exit()
    acceptor = Acceptor(sys.argv[1])
    acceptor.stay_alive()
