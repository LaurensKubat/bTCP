#!/usr/bin/env python3

import socket
import argparse
import bTCP.bTCPbase
import bTCP.packet

# Handle arguments
parser = argparse.ArgumentParser()
parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
parser.add_argument("-o", "--output", help="Where to store file", default="tmp.file")
args = parser.parse_args()

timeout = 100

server_ip = "127.0.0.1"
server_port = 9001

# Define a header format
header_format = "I"

SYNACK = 1
NORMAL = 2
FINACK = 3


# Server is the server, it inherits from bTCP, which implements basic bTCP functions
class Server(object):

    def __init__(self, baseTCP: bTCP.bTCPbase.BasebTCP):
        self.base = baseTCP

    # listen to the socket
    def listen(self):
        while True:
            packet = bTCP.packet.Packet()
            data, addr = self.base.sock.recvfrom(1016)
            packet.unpack(data)
            self.base.handle(packet)
            self.base.checksent()
            for id, con in self.base.cons:
                self.reassemble(id)

    def reassemble(self, stream_id):
        cur_syn = self.base.cur_syn_numbers[stream_id]
        next_packet = self.base.get_next_packet(stream_id, cur_syn)
        if next_packet is not bTCP.bTCPbase.NOT_RECV:
            cur_syn += 1
            # write to the correct file






