import socket
import struct
import sys

from node import Node


class Proposer(object, Node):
    def __init__(self):
        super(Proposer, self).__init__('proposer')
        self.instance = 0
        self.leaders = {} #leader candidates
        self.leader = self._id #start as the leader
        # State has:
        #  {instance: {ballot, acceptor_messages, phase, timestamp}}
        self.state = {}
        # {instance: [msgs]}
        self.acceptor_messages = {}
        # {instance: [msgs]}
        self.acceptor_decide = {}

    def recv(self):
        print('recv')
        msg, addr = self.__recv_socket.recvfrom(1024) #TODO: Adjust buffer size?!
        return (msg, addr)