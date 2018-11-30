import socket
import struct
import sys
import pickle


from node import Node
from message import Message


class Client(Node):
    def __init__(self):
        super().__init__('clients')
        self.id = 0
        # self.leaders = {}
        self.leader = self.id
        # State has:
        #  {instance: {ballot, acceptor_messages, phase, timestamp}}
        self.state = {}
        # {instance: [msgs]}
        self.acceptor_messages = {}
        # {instance: [msgs]}
        self.acceptor_decide = {}

    def await_message(self):
        while True:
            val = input("write message to send: ")
            message = Message("0", None, None, val, None, None)
            self.send(message, "proposers")


if __name__ == '__main__':
    client = Client()
    client.await_message()
