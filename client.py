import sys

from node import Node
from message import Message


class Client(Node):
    def __init__(self, _id):
        super().__init__('clients')
        self.id = _id           # id of the client
        self.leader = self.id   # not used

    def await_user_input(self):
        while True:
            value = input("write message to send: ")
            message = Message(msg_type="0", v_val=value)
            self.send((None, message), "proposers")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the client")
        sys.exit()
    client = Client(sys.argv[1])
    client.await_user_input()
