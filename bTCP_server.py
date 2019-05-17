#!/usr/bin/env python3

import socket
import argparse
from bTCP.bTCPbaseRefactor import *
import bTCP.packet


# Server is the server, it decorates with bTCPBase, which implements basic bTCP functions.
class Server(object):

    def __init__(self, output: str, base: BasebTCP):
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
            # if received is not empty, reassemble all received ordered packets
            if self.base.received:
                highest_syn = max(self.base.received)
                self.reassemble(highest_syn)

    def reassemble(self, cur_syn_num: int):
        if self.base.check_syn_nums(cur_syn_num):
            # open the output file
            f = open(self.output, "ab+")
            for i in range(cur_syn_num):
                # get packet i from received.
                pkt = self.base.received.get(i, None)
                if pkt is None:
                    continue
                # write the contents of the packet to the file, we keep possible padding in mind.
                for j in range(pkt.header.data_length):
                    f.write(pkt.data[i])
                # remove the packet from the buffer.
                self.base.received.pop(i)
            # close output file.
            f.close()


server = Server("outputtest.txt", BasebTCP(own_port=6543, own_ip="127.0.0.1",
                                                timeout=100, window_size=100, dest_port=6542, dest_ip="127.0.0.1"))
server.listen()
