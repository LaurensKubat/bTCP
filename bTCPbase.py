#!/usr/bin/env python3

import socket
from bTCP.header import *
from bTCP.packet import *
import time


NOT_RECV = "not received"
INIT_SYN = 1


class BasebTCP(object):

    def __init__(self, port: int, ip: int, timeout: int, output: str, cons: dict, sent: dict, window_size = 100):
        self.port = port
        self.ip = ip
        self.packets = dict
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
        self.window_size = window_size

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
    # TODO if the ack is an ack for our fin_ack, close the conn
    def handle_ack(self, packet: Packet):
        # if the ACK SYN_number is not in our dictionary of sent messages, we ignore the ACK
        if packet.header.SYN_number not in self.sent:
            return
        # if the ACK SYN_number is in our dict of sent messages, we remove the the ACK SYN_number from our
        # dict
        self.sent.pop(packet.header)

    def send_syn(self):
        tosend = Packet()
        tosend.header.SYN_number = INIT_SYN
        tosend.header.flags = set_syn(tosend.header.flags)

    def send_syn_ack(self, packet: Packet):
        tosend = Packet()
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.SYN_number = packet.header.SYN_number + 1
        tosend.header.windows = self.window_size
        tosend.header.flags = set_syn(tosend.header.flags)
        tosend.header.flags = set_ack(tosend.header.flags)
        self.send(tosend)

    # TODO decide what to do when the checksum is not correct. Ignore the message or implement some sort of
    #  NACK to be more error resilient?
    # currently we ignore any incorrect message
    def send_nack(self, packet: Packet):
        return

    # send an ack message based on the received packet, acks are not saved in the sent dict.
    def send_ack(self, packet: Packet):
        tosend = Packet(b"")
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
                self.send(packet, self.port, self.ip)

    # TODO include port and ip in the use of send
    def send(self, packet: Packet, port, ip):
        packet.header.genchecksum()
        self.sock.sendto(packet.pack(), (port, ip))
        self.sent[packet.header] = (packet, time.time())

    def send_file(self, filename: str, stream_id: str):
        self.create_packets(filename)
        cur_packet = 1
        max_packet = cur_packet + self.window_size



    # read a file and create the corresponding packets with a max data_length of 1000 bytes.
    # This will be used by the party sending data
    def create_packets(self, filename: str):
        f = open(filename, "rb")
        data_length = 0
        syn_num = 3
        data = b""
        byte = f.read(1)
        while byte != b"":
            data = data + byte
            data_length += 1
            byte = f.read(1)
            # if we fully filled a data field, we create a packet
            if data_length == 1000:
                self.create_packet(data, syn_num, data_length)
                data_length = 0
                data = b""
        # if the last packet has less than 1000 bytes but more than 0, we still need to create
        # that packet
        if data_length > 0:
            self.create_packet(data, syn_num, data_length)
            data_length = 0
            data = b""

    # create packet creates a single packet and saves it in the packet dict
    # any header fields that are dependant on any identifiers related to the connection are not set
    def create_packet(self, data:bytes, syn_num, data_length) -> Packet:
        packet = Packet(data=data)
        packet.header.SYN_number = syn_num
        packet.header.data_length = data_length
        return packet

    # reassemble a file sent over the connection stream_id. Output is written to self.output filename
    def reassemble_file(self, stream_id):
        syn_num = 3
        f = open(self.output, "ab")
        packet = self.get_packet(stream_id, syn_num)
        # if the packet exists, append the data_length to the output file
        while packet is not NOT_RECV:
            f.write(packet.data[0:packet.header.data_length-1])
        f.close()

    # get_next_packet returns the packet following syn_number from stream_id (from the received packets)
    def get_packet(self, stream_id, syn_number):
        pack = self.cons[stream_id].get(syn_number, NOT_RECV)
        if pack is not NOT_RECV:
            self.cons[stream_id].pop(syn_number)
        return pack
