import socket
import argparse
import bTCP.packet
import time
import bTCP.header


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
    def handle(self, packet: bTCP.packet.Packet):
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
    def handle_ack(self, packet: bTCP.packet.Packet):
        # if the ACK SYN_number is not in our dictionary of sent messages, we ignore the ACK
        if packet.header.SYN_number not in self.sent:
            return
        # if the ACK SYN_number is in our dict of sent messages, we remove the the ACK SYN_number from our
        # dict
        self.sent.pop(packet.header)

    def send_syn_ack(self, packet: bTCP.packet.Packet):
        tosend = bTCP.packet.Packet()
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.SYN_number = packet.header.SYN_number + 1
        tosend.header.flags = bTCP.header.set_syn(tosend.header.flags)
        tosend.header.flags = bTCP.header.set_ack(tosend.header.flags)
        self.send(tosend)

    # TODO decide what to do when the checksum is not correct. Ignore the message or implement some sort of
    #  NACK to be more error resilient?
    def send_nack(self, packet: bTCP.packet.Packet):
        return

    # send an ack message based on the received packet, acks are not saved in the sent dict.
    def send_ack(self, packet: bTCP.packet.Packet):
        tosend = bTCP.packet.Packet()
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.SYN_number = packet.header.SYN_number
        tosend.header.ACK_number = tosend.header.SYN_number
        tosend.header.flags = bTCP.header.set_ack(tosend.header.flags)
        self.sock.send(tosend.pack())

    # handle a received fin message
    def handle_fin(self, packet: bTCP.packet.Packet):
        tosend = bTCP.packet.Packet()
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.ACK_number = packet.header.SYN_number
        tosend.header.flags = bTCP.header.set_fin(tosend.header.flags)
        tosend.header.flags = bTCP.header.set_ack(tosend.header.flags)
        self.send(tosend)

    # check whether any sent messages are lost
    def checksent(self):
        for key, value in self.sent:
            packet, packtype, time = value
            elapsed =  time.time() - time
            if elapsed > self.timeout:
                self.send(packet)

    def send(self, packet: bTCP.packet.Packet):
        self.sock.send(packet.pack())
        self.sent[packet.header] = (packet, time.time())
