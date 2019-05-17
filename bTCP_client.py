#!/usr/bin/env python3

import socket, argparse
import random
from struct import *
from bTCP.bTCPbaseRefactor import *


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
        while True:
            try:
                data, addr = self.base.sock.recvfrom(1016)
                pkt = Packet(b"")
                pkt.unpack(data)
                self.base.handle(pkt)
                print("received syn response")
                break
            except socket.error:
                self.base.check_sent()
        # send the packets if to_send is not empty
        print("starting file transfer")
        while self.to_send:
            print(len(self.to_send))
            self.send_packets()
            wait = time.time()
            # recv from socket until timeout is reached, after we resend packets
            # TODO change this timeout wait to a spinning wait
            while time.time() - wait < self.timeout:
                try:
                    data, addr = self.base.sock.recvfrom(1016)
                    pkt = Packet(b"")
                    pkt.unpack(data)
                    self.base.handle(pkt)
                except socket.error:
                    pass
        # we close the connection
        print("sending fin")
        self.send_fin()
        print("starting to wait for fin_ack")
        while True:
            try:
                data, addr = self.base.sock.recvfrom(1016)
                pkt = Packet(b"")
                pkt.unpack(data)
                self.base.handle(pkt)
                print("received fin_ack response")
            except socket.error:
                self.base.check_sent()

    def send_packets(self):
        lowest_pkt = min(self.to_send)
        for i in range(lowest_pkt, lowest_pkt + self.base.window_size):
            pkt = self.to_send.get(i, None)
            if pkt is not None:
                pkt.header.SYN_number = self.base.syn_ack + i + 1
                self.base.send(self.to_send[i])

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
            self.to_send.update({pkt_num: pkt})
            total_packets = total_packets + 1
        print(total_packets)
        print(len(self.to_send))
        self.total_packets = total_packets
        f.close()


client = Client(filename="test.txt", timeout=100,
                base=BasebTCP(own_port=6542, own_ip="localhost",
                              timeout=100, window_size=100, dest_port=6543, dest_ip="localhost"))
client.send_file()
