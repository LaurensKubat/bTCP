#!/usr/bin/env python3

from bTCP.header import *


class Packet:

    def __init__(self, data: bytes, header=Header()):
        self.header = header
        self.data = data

    # TODO check that the length of the data packet is the same as the data length header field
    def validate(self) -> bool:
        correct = (len(self.data) == self.header.data_length)
        return correct and self.header.validate()

    # TODO evaluate whether there should be some runtime evaluation
    def unpack(self, pack: bytes):
        self.header = new_header(pack[0:16])
        self.data = pack[16:]

    # TODO check if this needs to use struct
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
