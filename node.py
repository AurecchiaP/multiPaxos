import socket
import struct
import os


def load_config():
    conf = {}
    with open(os.getcwd() + '/config.ini') as f:
        for line in f:
            conf_line = line.split()
            conf[conf_line[0]] = conf_line[1:]
    return conf


config = load_config()


class Node:
    def __init__(self, role):
        self.role = role
        self.multicast_group = tuple(config[self.role])
        self.recv_sock = self.create_socket(self.multicast_group[0])

    def create_socket(self, dst):
        # Create the datagram socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                        struct.pack('4sL', socket.inet_aton(dst), socket.INADDR_ANY))
        # sock.settimeout(0.2)
        return sock

    def send(self, msg, dst):
        print("sending")
        msg = msg.SerializeToString()

        # if the destination is to my same role (acceptor, proposer, learner)
        if dst == self.role:
            return self.recv_sock.sendto(msg, self.multicast_group)
        else:
            send_sock = self.create_socket(config[dst][0])
            send_sock.sendto(msg, tuple(config[dst]))
            send_sock.close()

    def recv(self):
        print("receiving")
        msg, addr = self.recv_sock.recvfrom(1024)
        return msg, addr
