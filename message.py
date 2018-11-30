class Message:
    def __init__(self, msg_type, ballot, v_rnd, v_val, c_rnd, c_val):
        self.msg_type = msg_type
        self.ballot = ballot
        self.v_rnd = v_rnd
        self.v_val = v_val
        self.c_rnd = c_rnd
        self.c_val = c_val

    def to_string(self):
        return ', '.join(filter(None, (self.msg_type,
                                       str(self.ballot),
                                       str(self.v_rnd),
                                       str(self.v_val),
                                       str(self.c_rnd),
                                       str(self.c_val))
                                )
                         )
