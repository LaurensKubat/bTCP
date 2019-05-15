#!/usr/bin/env python3

import socket
import argparse
import bTCP.bTCPbaseRefactor
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

# Define a header format.
header_format = "I"

SYNACK = 1
NORMAL = 2
FINACK = 3


# Server is the server, it decorates with bTCPBase, which implements basic bTCP functions.
class Server(object):

    def __init__(self, output: str, base: bTCP.bTCPbaseRefactor.BasebTCP):
        self.base = base
        self.output = output

    # listen to the socket.
    def listen(self):
        while True:
            packet = bTCP.packet.Packet(b"")
            data, addr = self.base.sock.recvfrom(1016)
            packet.unpack(data)
            self.base.handle(packet)
            self.base.check_sent()
            highest_syn = max(self.base.received)
            self.reassemble(highest_syn)

    def reassemble(self, cur_syn_num: int):
        if self.base.check_syn_nums(cur_syn_num):
            # open the output file
            f = open(self.output, "ab+")
            for i in range(cur_syn_num):
                # get packet i from received.
                pkt = self.base.received[i]
                # write the contents of the packet to the file, we keep possible padding in mind.
                for j in range(pkt.header.data_length):
                    f.write(pkt.data[i])
                # remove the packet from the buffer.
                self.base.received.pop(i)
            # close output file.
            f.close()
