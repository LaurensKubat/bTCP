#!/usr/bin/env python3

import socket
from bTCPfolder.packet import *
import time


INIT_SYN = 1


class BasebTCP(object):

    def __init__(self, own_port: int, own_ip, timeout: int,
                 window_size=100, dest_port=0, dest_ip=0):
        self.port = own_port
        self.ip = own_ip
        self.packets = dict
        self.timeout = timeout
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
        self.syn_ack = 0
        self.connected = False

    # handle the packet based on the flags of the header packet
    def handle(self, packet: Packet):
        ok = packet.validate()
        if not ok:
            # for now, we ignore any packets and wait for the client to resend them
            print("not ok")
            self.send_nack(packet)
            # if we receive a syn ack, we ack this and set the window to the given window
        elif packet.is_syn() and packet.is_ack() and packet.header.stream_id == self.cur_stream_id:
            print("got syn ack over known conn")
            self.connected = True
            self.window_size = packet.header.windows
            self.syn_ack = packet.header.SYN_number
            print("syn_ack value is: " + str(self.syn_ack))
            self.send_ack(packet)

        # if we receive a SYN packet, and we are not connected, we set all setting and ack the syn
        elif packet.is_syn() and not packet.is_ack() and not self.connected:
            print("handling syn")
            self.cur_stream_id = packet.header.stream_id
            self.window_size = packet.header.windows
            self.syn_ack = packet.header.SYN_number
            self.connected = True
            self.send_syn_ack(packet)
        # if the packet is an ack of our current stream or an ack of a sent packet (of a previous conn possibly)
        # handle the ack
        elif packet.is_ack() and not packet.is_fin() and not packet.is_syn() and packet.header.stream_id == self.cur_stream_id:
               # or ((packet.header.stream_id, packet.header.ACK_number) in self.sent):
            print("received ack")
            self.handle_ack(packet)

        elif packet.header.is_fin() and not packet.is_ack() and packet.header.stream_id == self.cur_stream_id:
            print("god knows why i am here")
            self.handle_fin(packet)
        elif packet.header.is_fin() and packet.is_ack() and packet.header.stream_id == self.cur_stream_id:
            print("fuck me mate")
            self.send_ack(packet=packet)
            self.cur_stream_id = 0
            self.connected = False
        else:
            print("reached else")

            # if the connection isn't established yet, ignore the packet
            if not self.connected:
                print("not connected")
                return
            # if we receive a package from a different stream, we ignore it
            if not packet.header.stream_id == self.cur_stream_id:
                print(packet.header.stream_id)
                print(self.cur_stream_id)
                print("received unknown packet")
                return
            # add the packet to the correct window, if the packet is not received yet
            if packet.header.SYN_number not in self.received:
                print("acking" + str(packet.header.SYN_number))
                self.send_ack(packet)
                self.received.update({packet.header.SYN_number: packet})
            else:
                print("no if entered!")
                print(packet.header.flags)
                print(packet.header.SYN_number)

    def send_nack(self, packet: Packet):
        return

    def send_ack(self, packet: Packet):
        print("sending ack")
        print(packet.header.SYN_number)
        tosend = Packet(data=b"")
        tosend.header.stream_id = packet.header.stream_id
        print("ACK: " + str(tosend.header.SYN_number))
        tosend.header.ACK_number = tosend.header.SYN_number
        tosend.header.SYN_number = 0
        # reset the flags of the packet we are acking, if we want to send a syn_Ack of fin_ack we need to use
        # the dedicated functions.
        tosend.header.flags = 0
        tosend.header.flags = set_ack(tosend.header.flags)
        self.send(tosend)

    def send_syn(self, stream_id, windows):
        tosend = Packet(data=b"")
        tosend.header.windows = windows
        tosend.header.stream_id = stream_id
        tosend.header.SYN_number = INIT_SYN
        tosend.header.flags = set_syn(tosend.header.flags)
        self.sent.update({tosend.header.SYN_number: (tosend, time.time())})
        self.send(tosend)

    def send_syn_ack(self, packet: Packet):
        # we create the ack packet
        tosend = Packet(data=b"")
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.ACK_number = packet.header.SYN_number
        tosend.header.SYN_number = packet.header.SYN_number + 1
        print(tosend.header.SYN_number)
        if packet.header.windows >= self.window_size:
            tosend.header.windows = self.window_size
        else:
            tosend.header.windows = packet.header.windows
        tosend.header.flags = 0
        tosend.header.flags = set_syn(tosend.header.flags)
        tosend.header.flags = set_ack(tosend.header.flags)
        print("sending syn_ack")
        self.syn_ack = tosend.header.SYN_number
        self.sent.update({tosend.header.SYN_number: (tosend, time.time())})
        self.send(tosend)

    def handle_ack(self, packet: Packet):
        # if the ACK SYN_number is not in our dictionary of sent messages, we ignore the ACK
        # if the ACK SYN_number is in our dict of sent messages, we remove the the ACK SYN_number from our
        # dict
        print(packet.header.ACK_number)
        self.sent.pop(packet.header.ACK_number)

        # handle a received fin message
        # if all the syn numbers are consecutive,

    # if we receive a fin, we send a fin ack close the connection and return to listen on the port
    def handle_fin(self, packet: Packet):
        if self.check_syn_nums(packet.header.SYN_number):
            self.send_fin_ack(packet)
            self.cur_stream_id = 0
            self.connected = False

    def send_fin(self, syn_number):
        tosend = Packet(data=b"")
        tosend.header.stream_id = self.cur_stream_id
        tosend.header.SYN_number = syn_number
        tosend.header.windows = self.window_size
        tosend.header.data_length = 0
        tosend.header.flags = set_fin(tosend.header.flags)
        self.sent.update({tosend.header.SYN_number: (tosend, time.time())})
        self.send(tosend)

    def send_fin_ack(self, packet: Packet):
        tosend = Packet(data=b"")
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.ACK_number = packet.header.SYN_number
        tosend.header.flags = set_fin(tosend.header.flags)
        tosend.header.flags = set_ack(tosend.header.flags)
        self.sent.update({tosend.header.SYN_number: (tosend, time.time())})
        self.send(tosend)

    # check if we are missing any packages by checking that all the syn numbers are consecutive
    # TODO this might fail due to the way a connections is initiated.
    def check_syn_nums(self, fin_syn_num: int) -> bool:
        pkt = INIT_SYN
        while pkt < fin_syn_num:
            packet = self.received.get(pkt, None)
            if packet is None:
                return False
        return True

    def check_sent(self):
        for pkt_id in self.sent:
            packet, sent_time = self.sent[pkt_id]
            # if more than 5 seconds have elapsed since the packet is sent
            if time.time() - sent_time > 5:
                self.send(packet)

    def send(self, packet: Packet):
        packet.header.stream_id = self.cur_stream_id
        packet.header.genchecksum()
        self.sock.sendto(packet.pack(), (self.dest_ip, self.dest_port))
