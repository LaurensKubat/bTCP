#!/usr/bin/env python3

import socket, argparse
import random
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

    def __init__(self, filename: str, base: BasebTCP, timeout: int):
        self.base = base
        self.filename = filename
        self.to_send = {}
        # we set the socket to non blocking
        self.base.sock.setblocking(0)
        self.timeout = timeout
        self.total_packets = 0

    def send_file(self):
        self.create_packets()
        self.send_syn()
        # we try to connect, wait for the timeout period, if we received nothing, we resend the syn with check_sent()
        time.sleep(self.timeout)
        while True:
            try:
                data, addr = self.base.sock.recvfrom(1016)
                pkt = Packet(b"")
                pkt.unpack(data)
                self.base.handle(pkt)
                break
            except socket.error:
                self.base.check_sent()
        # send the packets if to_send is not empty
        while not self.to_send:
            self.send_packets()
            wait = time.time()
            # recv from socket until timeout is reached, after we resend packets
            while time.time() - wait < self.timeout:
                try:
                    data, addr = self.base.sock.recvfrom(1016)
                    pkt = Packet(b"")
                    pkt.unpack(data)
                    self.base.handle(pkt)
                except socket.error:
                    pass
        # we close the connection
        self.send_fin()

    def send_packets(self):
        lowest_pkt = min(self.to_send)
        for i in range(lowest_pkt, lowest_pkt + self.base.window_size):
            pkt = self.to_send[i]
            pkt.header.SYN_number = self.base.syn_ack + i + 1
            self.base.send(self.to_send[i])

    def send_syn(self):
        stream_id = random.randint(0, 65535)
        self.base.cur_stream_id = stream_id
        self.base.window_size = args[0]
        self.base.send_syn(stream_id, self.base.window_size)

    def send_fin(self):
        self.base.send_fin(self.base.syn_ack + self.total_packets + 1)

    def create_packets(self):
        f = open(self.filename, "rb")
        byte = f.read(1)
        data_length = 0
        pkt_num = 1
        total_packets = 0
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
                self.to_send.update({pkt_num, (pkt, False, False)})
                total_packets = total_packets + 1
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
            self.to_send.update({pkt_num, (pkt, False, False)})
            total_packets = total_packets + 1
        self.total_packets = total_packets
        f.close()
