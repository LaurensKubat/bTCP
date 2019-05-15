#!/usr/bin/env python3

import socket, argparse
from struct import *
from bTCP.bTCPbaseRefactor import *

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


class Client(object):

    def __init__(self, filename: str, base: BasebTCP):
        self.base = base
        self.filename = filename
        self.tosend = {}

    def send_file(self):
        self.create_packets()

    def send_syn(self):
        syn_pkt = Packet(b"")


    def create_packets(self):
        f = open(self.filename, "rb")
        byte = f.read(1)
        data_length = 0
        pkt_num = 1
        data = b""
        while byte != b"":
            data = data + byte
            data_length = data_length + 1
            # if we have read byte one thousand, we create a packet
            if data_length == 1000:
                pkt = Packet(data)
                pkt.header.data_length = data_length
                # we save the created packets without header in the format: Packet_number (packet
                # 1 was created first); Packet, is sent, is acked.
                self.tosend.update({pkt_num, (pkt, False, False)})
                pkt_num = pkt_num + 1
                data_length = 0
                data = b""
            byte = f.read(1)
        # if we are done reading, but still have less than 1000 bytes left over, we create
        # another packet
        if data_length > 0:
            pkt = Packet(data)
            pkt.header.data_length = data_length
            # we save the created packets without header in the format: Packet_number (packet
            # 1 was created first); Packet, is sent, is acked.
            self.tosend.update({pkt_num, (pkt, False, False)})
        f.close()
