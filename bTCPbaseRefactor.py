#!/usr/bin/env python3

import socket
from bTCP.header import *
from bTCP.packet import *
import time


INIT_SYN = 1


class BasebTCP(object):

    def __init__(self, own_port: int, own_ip: int, timeout: int, output: str,
                 window_size=100, dest_port=0, dest_ip=0):
        self.port = own_port
        self.ip = own_ip
        self.packets = dict
        self.timeout = timeout
        self.output = output
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock = sock
        self.sock.bind((own_ip, own_port))
        self.sent = {}
        self.received = {}
        self.timeout = timeout
        self.window_size = window_size
        self.dest_port = dest_port
        self.dest_ip = dest_ip
        self.cur_stream_id = 0
        self.connected = False

    # handle the packet based on the flags of the header packet
    def handle(self, packet: Packet):
        ok = packet.validate()
        if not ok:
            # for now, we ignore any packets and wait for the client to resend them
            self.send_nack(packet)
            # if we receive a syn ack, we ack this and set the window to the given window
        elif packet.is_syn() and packet.is_ack() and packet.header.stream_id == self.cur_stream_id:
            self.window_size = packet.header.windows
            self.send_ack(packet)

        # if we receive a SYN packet, and we are not connected, we set all setting and ack the syn
        elif packet.is_syn() and not packet.is_ack() and not self.connected:
            self.cur_stream_id = packet.header.stream_id
            self.connected = True
            self.send_syn_ack(packet)
        # if the packet is an ack of our current stream or an ack of a sent packet (of a previous conn possibly)
        # handle the ack
        elif (packet.is_ack() and not packet.is_fin() and packet.header.stream_id == self.cur_stream_id) \
                or ((packet.header.stream_id, packet.header.ACK_number) in self.sent):
            self.handle_ack(packet)
        elif packet.header.is_fin() and not packet.is_ack() and packet.header.stream_id == self.cur_stream_id:
            self.handle_fin(packet)
        elif packet.header.is_fin() and packet.is_ack() and packet.header.stream_id == self.cur_stream_id:
            self.send_ack(packet=packet)
            self.cur_stream_id = 0
            self.connected = False

        else:
            # if the connection isn't established yet, ignore the packet
            if not self.connected:
                return
            # if we receive a package from a different stream, we ignore it
            if packet.header.stream_id is not self.cur_stream_id:
                return
            # add the packet to the correct window, if the packet is not received yet
            if packet.header.SYN_number not in self.received:
                self.send_ack(packet)
                self.received.update({packet.header.SYN_number, packet})

    def send_nack(self, packet: Packet):
        return

    def send_ack(self, packet: Packet):
        tosend = Packet(data=b"")
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.SYN_number = packet.header.SYN_number
        tosend.header.ACK_number = tosend.header.SYN_number
        tosend.header.flags = set_ack(tosend.header.flags)
        self.send(tosend)

    def send_syn(self):
        tosend = Packet(data=b"")
        tosend.header.stream_id = self.port
        tosend.header.SYN_number = INIT_SYN
        tosend.header.flags = set_syn(tosend.header.flags)
        self.send(tosend)

    def send_syn_ack(self, packet: Packet):
        # we create the ack packet
        tosend = Packet(data=b"")
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.SYN_number = packet.header.SYN_number + 1
        tosend.header.windows = self.window_size
        tosend.header.flags = set_syn(tosend.header.flags)
        tosend.header.flags = set_ack(tosend.header.flags)
        self.send(tosend)

    def handle_ack(self, packet: Packet):
        # if the ACK SYN_number is not in our dictionary of sent messages, we ignore the ACK
        if packet.header.SYN_number not in self.sent:
            return
        # if the ACK SYN_number is in our dict of sent messages, we remove the the ACK SYN_number from our
        # dict
        self.sent.pop(packet.header)

        # handle a received fin message
        # if all the syn numbers are consecutive,

    # if we receive a fin, we send a fin ack close the connection and return to listen on the port
    def handle_fin(self, packet: Packet):
        if self.check_syn_nums(packet.header.SYN_number):
            self.send_fin_ack(packet)
            self.cur_stream_id = 0
            self.connected = False

    def send_fin_ack(self, packet: Packet):
        tosend = Packet(data=b"")
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.ACK_number = packet.header.SYN_number
        tosend.header.flags = set_fin(tosend.header.flags)
        tosend.header.flags = set_ack(tosend.header.flags)
        self.send(tosend)

    # check if we are missing any packages by checking that all the syn numbers are consecutive
    # TODO this might fail due to the way a connections is initiated.
    def check_syn_nums(self, fin_syn_num: int) -> bool:
        pkt = INIT_SYN
        while pkt < fin_syn_num:
            packet = self.received[pkt]
            if packet is None:
                return False
        return True

    def check_sent(self):
        for pkt_id in self.sent:
            packet, senttime = self.sent[pkt_id]
            # if more than 5 seconds have elapsed since the packet is sent
            if time.time() - senttime > 5:
                self.send(packet)

    def send(self, packet: Packet):
        packet.header.genchecksum()
        self.sock.sendto(packet.pack(), (self.dest_ip, self.dest_port))