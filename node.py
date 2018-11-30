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
        self.role = role
        self.multicast_group = tuple(config[self.role])
        self.recv_sock = self.create_socket(self.multicast_group[0])
        self.recv_sock.bind(self.multicast_group)

    def create_socket(self, dst):
        # Create the datagram socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                        struct.pack('4sL', socket.inet_aton(dst), socket.INADDR_ANY))
        return sock

    def send(self, msg, dst):
        # print("Sending: message to " + dst)
        data = pickle.dumps(msg)

        # if the destination is to my same role (acceptors, proposers, learners)
        if dst == self.role:
            return self.recv_sock.sendto(data, self.multicast_group)
        else:
            send_sock = self.create_socket(config[dst][0])
            print("sending to " + str(config[dst][0]) + " " + str(config[dst][1]))
            send_sock.sendto(data, tuple(config[dst]))
            send_sock.close()

    def recv(self):
        # print("receiving")
        data, addr = self.recv_sock.recvfrom(1024)
        return data, addr
