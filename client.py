from node import Node
from message import Message


class Client(Node):
    def __init__(self):
        super().__init__('clients')
        self.id = 0
        self.leader = self.id
        self.state = {}

    def await_message(self):
        while True:
            val = input("write message to send: ")
            message = Message("0", None, None, val, None, None)
            self.send((None, message), "proposers")


if __name__ == '__main__':
    client = Client()
    client.await_message()
