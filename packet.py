import bTCP.header.py


class Packet:

    def __init__(self, header, data):
        self.header = header
        self.data = data

    def validate(self) -> bool:
        correct = True
        correct & self.header.validate()

        return correct

    def unpack(self, pack: bytes):
        self.header = bTCP.header.new_header(pack[0:16])
        self.data = pack[16:]
