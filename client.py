from node import Node
from message import Message


class Client(Node):
    def __init__(self):
        super().__init__('clients')
        self.id = 0             # id of the client
        self.leader = self.id   # not used

    def await_user_input(self):
        while True:
            value = input("write message to send: ")
            message = Message(msg_type="0", v_val=value)
            self.send((None, message), "proposers")


if __name__ == '__main__':
    client = Client()
    client.await_user_input()
