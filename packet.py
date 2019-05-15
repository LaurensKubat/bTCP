#!/usr/bin/env python3

from bTCP.header import *


class Packet:

    def __init__(self, data: bytes, header=Header()):
        self.header = header
        self.data = data

    def validate(self) -> bool:
        correct = (len(self.data) == self.header.data_length)
        return correct and self.header.validate()

    def unpack(self, pack: bytes):
        self.header = new_header(pack[0:16])
        self.data = pack[16:]

    # TODO check if this needs to use struct
    def pack(self) -> bytes:
        buf = b""
        buf += self.header.serialize()
        buf += self.data
        # pad the packet if needed
        if self.header.data_length < 1000:
            buf += b'0' * (1000 - self.header.data_length)
        return buf

    # is_'flag' functions are not tested in the unittests since they are tested in the header functions
    def is_syn(self):
        return self.header.is_syn()

    def is_ack(self):
        return self.header.is_ack()

    def is_fin(self):
        return self.header.is_fin()
