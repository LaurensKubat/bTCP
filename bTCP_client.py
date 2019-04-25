#!/usr/bin/env python3

import socket, argparse
from struct import *
from bTCP import bTCPbase
from bTCP.header import *

# Handle arguments
parser = argparse.ArgumentParser()
parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
parser.add_argument("-i","--input", help="File to send", default="tmp.file")
args = parser.parse_args()

destination_ip = "127.0.0.1"
destination_port = 9001

# bTCP header
header_format = "I"
bTCP_header = pack(header_format, 1)
bTCP_payload = ""
udp_payload = bTCP_header

# UDP socket which will transport your bTCP packets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# send payload
sock.sendto(udp_payload, (destination_ip, destination_port))


# TODO add fragmenting of a file, keeping track of the window and sending messages according to the window.
class Client(object):

    def __init__(self, port, ip, window, timeout, output, stream_id, cons: dict, sent: dict):
        self.base = bTCPbase.BasebTCP(port, ip, window, timeout, output, cons, sent)
        self.cur_syn = 0
        self.min_window = 0
        self.max_window = 0
        self.stream_id = stream_id

    # get_header in the client package should never handle flags, this is done in the bTCPbase
    # or in the function getting the header
    # the client does not have any windows in it's headers
    def get_header(self, data_length: int) -> Header:
        h = Header()
        h.SYN_number = self.cur_syn
        h.stream_id = self.stream_id
        h.data_length = data_length
        h.genchecksum()

        return h

    def openfile(self, filename):
        f = open(filename, "rb")
        try:
            data = f.read(1000)
            packet =
        finally:
            f.close()