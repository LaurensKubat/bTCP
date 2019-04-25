#!/usr/bin/env python3

import socket
from bTCP.header import *
from bTCP.packet import *
import time


NOT_RECV = "not received"
INIT_SYN = 1

class BasebTCP(object):

    def __init__(self, port, ip, window, timeout, output, cons: dict, sent: dict):
        self.port = port
        self.ip = ip
        self.window = window
        self.cur_syn_numbers = {}
        self.timeout = timeout
        self.output = output
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock = sock
        self.sock.bind((ip, port))
        # cons is a dict containing dicts for each connection. The second level dictionary contains
        # WINDOW SIZE amount of packages
        self.cons = cons
        self.sent = sent
        self.timeout = timeout

    # handle the packet based on the flags of the header packet
    # TODO add handling of FIN
    def handle(self, packet: Packet):
        ok = packet.validate()
        if not ok:
            # for now, we ignore any packets and wait for the client to resend them
            self.send_nack(packet)
        elif packet.is_syn() and packet.is_ack():
            self.send_ack(packet)
        elif packet.is_syn() and not packet.is_ack():
            # all new established connections are indexed by the stream id, the packets are saved in the
            # second level dict, the lowest SYN number is saved in the cur_syn_numbers dict
            self.send_syn_ack(packet)
            self.cons[packet.header.stream_id] = {packet.header.SYN_number: packet}
            self.cur_syn_numbers[packet.header.stream_id] = packet.header.SYN_number
        elif packet.is_ack():
            self.handle_ack(packet)
        elif packet.header.is_fin():
            self.handle_fin(packet)
        else:
            # if the connection isn't established yet, ignore the packet
            if packet.header.stream_id not in self.cons:
                return
            # add the packet to the correct window
            if packet.header.SYN_number not in self.cons[packet.header.stream_id]:
                self.send_ack(packet)
                self.cons[packet.header.stream_id].update({packet.header.SYN_number: packet})

    # handle a received ACK
    def handle_ack(self, packet: Packet):
        # if the ACK SYN_number is not in our dictionary of sent messages, we ignore the ACK
        if packet.header.SYN_number not in self.sent:
            return
        # if the ACK SYN_number is in our dict of sent messages, we remove the the ACK SYN_number from our
        # dict
        self.sent.pop(packet.header)

    # TODO set the correct window
    def send_syn_ack(self, packet: Packet):
        tosend = Packet()
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.SYN_number = packet.header.SYN_number + 1
        tosend.header.flags = set_syn(tosend.header.flags)
        tosend.header.flags = set_ack(tosend.header.flags)
        self.send(tosend)

    # TODO decide what to do when the checksum is not correct. Ignore the message or implement some sort of
    #  NACK to be more error resilient?
    def send_nack(self, packet: Packet):
        return

    # send an ack message based on the received packet, acks are not saved in the sent dict.
    def send_ack(self, packet: Packet):
        tosend = Packet()
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.SYN_number = packet.header.SYN_number
        tosend.header.ACK_number = tosend.header.SYN_number
        tosend.header.flags = set_ack(tosend.header.flags)
        self.sock.send(tosend.pack())

    # handle a received fin message
    # if all the syn numbers are consecutive,
    def handle_fin(self, packet: Packet):
        if self.checksynnums(packet.header.stream_id, packet.header.SYN_number):
            tosend = Packet(data=b"")
            tosend.header.stream_id = packet.header.stream_id
            tosend.header.ACK_number = packet.header.SYN_number
            tosend.header.flags = set_fin(tosend.header.flags)
            tosend.header.flags = set_ack(tosend.header.flags)
            self.send(tosend)

    # check if we are missing any packages by checking that all the syn numbers are consecutive
    # this might fail due to the way a connections is initiated.
    def checksynnums(self, stream_id, fin_syn_num: int) -> bool:
        cur_syn = INIT_SYN
        while cur_syn in self.cons[stream_id]:
            cur_syn += 1
        return cur_syn == fin_syn_num


    # check whether any sent messages are lost
    def checksent(self):
        for key, value in self.sent:
            packet, senttime = value
            elapsed = time.time() - senttime
            if elapsed > self.timeout:
                self.send(packet)

    # TODO include port and ip in the use of send
    def send(self, packet: Packet, port, ip):
        self.sock.sendto(packet.pack(), (port, ip))
        self.sent[packet.header] = (packet, time.time())

    # get_next_packet returns the packet following syn_number from stream_id (from the received packets)
    def get_next_packet(self, stream_id, syn_number):
        pack = self.cons[stream_id].get(syn_number + 1, NOT_RECV)
        if pack is not NOT_RECV:
            self.cons[stream_id].pop(syn_number + 1)
        return pack
