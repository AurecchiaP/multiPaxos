import socket
import struct
import os
import pickle


def load_config():
    conf = {}
    with open(os.getcwd() + '/config.conf') as f:
        for line in f:
            conf_line = line.split()
            conf[conf_line[0]] = [conf_line[1], int(conf_line[2])]
    return conf


config = load_config()


class Node:
    def __init__(self, role):
        self.role = role                                         # one between clients, proposers, acceptors, learners
        self.group = tuple(config[self.role])                    # the (ip, port) of the group
        self.receive_socket = self.create_socket(self.group[0])  # socket used to receive messages
        self.receive_socket.bind(self.group)

    @staticmethod
    def create_socket(dst):
        # Create the datagram socket
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        new_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))
        new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        new_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                              struct.pack('4sL', socket.inet_aton(dst), socket.INADDR_ANY))
        return new_socket

    def send(self, message, dst):
        data = pickle.dumps(message)

        # if the destination is to my same role
        if dst == self.role:
            send_socket = self.create_socket(config[dst][0])
            send_socket.sendto(data, self.group)
        else:
            send_socket = self.create_socket(config[dst][0])
            send_socket.sendto(data, tuple(config[dst]))
            send_socket.close()

    def receive(self):
        data, address = self.receive_socket.recvfrom(4096)
        instance, message = pickle.loads(data)
        return instance, message
