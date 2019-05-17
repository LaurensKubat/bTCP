#!/usr/bin/env python3

import socket, argparse
import random
from struct import *
from bTCP.bTCPbaseRefactor import *


class Client(object):

    def __init__(self, filename: str, base: BasebTCP, timeout: int):
        self.base = base
        self.filename = filename
        # we set the socket to non blocking
        self.base.sock.setblocking(0)
        self.timeout = timeout
        self.total_packets = 0

    def send_file(self):
        self.create_packets()
        self.send_syn()
        # we try to connect, wait for the timeout period, if we received nothing, we resend the syn with check_sent()
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
        print("starting file transfer")
        while self.base.sent:
            print(len(self.base.sent))
            self.send_packets()
            wait = time.time()
            # recv from socket until timeout is reached, after we resend packets. If all sent messages are acked, we
            # continue to send more messages
            while time.time() - wait < self.timeout:
                try:
                    data, addr = self.base.sock.recvfrom(1016)
                    pkt = Packet(b"")
                    pkt.unpack(data)
                    self.base.handle(pkt)
                except socket.error:
                    pass
                if not self.base.sent:
                    break
        # we close the connection
        print("sending fin")
        self.send_fin()
        print("starting to wait for fin_ack")
        wait = time.time()
        while time.time() - wait < self.timeout:
            try:
                data, addr = self.base.sock.recvfrom(1016)
                pkt = Packet(b"")
                pkt.unpack(data)
                self.base.handle(pkt)
                print("received fin_ack response")
                break
            except socket.error:
                self.base.check_sent()

    def send_packets(self):
        lowest_pkt = min(self.base.sent.keys())
        for i in range(lowest_pkt, lowest_pkt + self.base.window_size):
            (pkt_num, (pkt, time_sent)) = self.base.sent.get(i, (-1, ("a", 2)))
            if pkt_num is not -1:
                pkt.header.SYN_number = self.base.syn_ack + i + 1
                print("start data packets")
                print(pkt.header.flags)
                print("end data packets")
                self.base.send(pkt)

    def send_syn(self):
        stream_id = random.randint(0, 65535)
        self.base.cur_stream_id = stream_id
        self.base.window_size = 100
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
                pkt = Packet(data=data)
                pkt.header.data_length = data_length
                # we save the created packets without header in the format: Packet_number (packet
                # 1 was created first); Packet, is sent, is acked.
                self.base.sent.update({pkt_num, (pkt, time.time())})
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
            pkt.header.flags = 0
            # we save the created packets without header in the format: Packet_number (packet
            # 1 was created first); Packet, is sent, is acked.
            self.base.sent.update({pkt_num: (pkt, time.time())})
            total_packets = total_packets + 1
        print(total_packets)
        print(len(self.base.sent))
        self.total_packets = total_packets
        f.close()


client = Client(filename="test.txt", timeout=100,
                base=BasebTCP(own_port=6542, own_ip="localhost",
                              timeout=100, window_size=100, dest_port=6543, dest_ip="localhost"))
client.send_file()
