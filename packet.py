#!/usr/bin/env python3

from header import *


class Packet:

    def __init__(self, data: bytes, header=Header()):
        self.header = header
        self.data = data

    def validate(self) -> bool:
        # correct = (len(self.data) == self.header.data_length)
        # removed validation of the data length since i decided to pad the messages
        return self.header.validate(self.data)

    def unpack(self, pack: bytes):
        self.header = new_header(pack[:16])
        self.data = pack[16:]

    def pack(self) -> bytes:
        buf = b""
        buf += self.header.serialize()
        buf += self.data
        return buf

    # is_'flag' functions are not tested in the unittests since they are tested in the header functions
    def is_syn(self):
        return self.header.is_syn()

    def is_ack(self):
        return self.header.is_ack()

    def is_fin(self):
        return self.header.is_fin()
