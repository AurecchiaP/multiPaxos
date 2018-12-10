import sys
import time

from node import Node
from message import Message


class Client(Node):
    def __init__(self, _id):
        super().__init__('clients')
        self.id = _id           # id of the client
        # self.count = 0

    def await_user_input(self):
        try:
            while True:
                # value = input("write message to send: ")
                value = input()
                message = Message(msg_type="0", v_val=value)
                self.send((None, message), "proposers")
                # if we run the whole thing on one machine, this may avoid the OS getting overfilled with messages
                # self.count += 1
                # if self.count == 250:
                #     self.count = 0
                #     time.sleep(.5)
        except EOFError:
            print("EOF reached")
            sys.exit()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("give the id of the client")
        sys.exit()
    client = Client(sys.argv[1])
    client.await_user_input()
