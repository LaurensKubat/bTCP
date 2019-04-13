#!/usr/bin/env python3

import bTCP.header.py


class Packet:

    def __init__(self, header=bTCP.header.new_header(), data=0):
        self.header = header
        self.data = data

    # TODO check that the length of the data packet is the same as the data length header field
    def validate(self) -> bool:
        correct = True
        correct & self.header.validate()

        return correct

    # TODO evaluate whether there should be some runtime evaluation
    def unpack(self, pack: bytes):
        self.header = bTCP.header.new_header(pack[0:16])
        self.data = pack[16:]

    # TODO check if this needs to use struct
    def pack(self) -> bytes:
        data = bytearray(self.header.serialize())
        data.append(self.data)
        return data

    def is_syn(self):
        return self.is_syn()

    def is_ack(self):
        return self.is_ack()

    def is_fin(self):
        return self.is_fin()
