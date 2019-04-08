import bTCP.header.py

class packet:
    def __init__(self, header, data):
        self.header = header
        self.data = data

    def validate(self) -> bool:
        return True

    def unpack(self, packet:bytes):
        self.header = bTCP.header.new_header(packet[0:16])
        self.data = packet[16:]