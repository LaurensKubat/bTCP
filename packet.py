import bTCP.header.py


class Packet:

    def __init__(self, header=bTCP.header.new_header(), data=0):
        self.header = header
        self.data = data

    def validate(self) -> bool:
        correct = True
        correct & self.header.validate()

        return correct

    def unpack(self, pack: bytes):
        self.header = bTCP.header.new_header(pack[0:16])
        self.data = pack[16:]

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
