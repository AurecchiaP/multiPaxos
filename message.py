class Message:

    # TODO instance atm not used
    def __init__(self, **kwargs):
        self.msg_type = kwargs.pop('msg_type', None)
        self.instance = kwargs.pop('instance', None)
        self.leader = kwargs.pop('leader', None)
        self.id = kwargs.pop('id', None)
        self.ballot = kwargs.pop('ballot', 0)
        self.v_rnd = kwargs.pop('v_rnd', 0)
        self.v_val = kwargs.pop('v_val', None)
        self.c_rnd = kwargs.pop('c_rnd', 0)
        self.c_val = kwargs.pop('c_val', None)

    def to_string(self):
        return "msg_type= {0}\nballot\t= {1}\nleader\t= {2}\nid\t= {3}\nv_rnd\t= {4}\nv_val\t= {5}" \
               "\nc_rnd\t= {6}\nc_val\t= {7}".format(self.msg_type, self.ballot, self.leader, self.id, self.v_rnd,
                                                     self.v_val, self.c_rnd, self.c_val)
