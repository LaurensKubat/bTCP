import socket
from bTCPfolder.packet import *
from bTCPfolder.header import *
from time import *
import random


SYN = 1
ACK = 2
FIN = 3
SYNACK = 4
FINACK = 5


class bTCP():
    def __init__(self, own_port, own_ip, filename, dest_ip, dest_port, window_size, timeout, initial_SYN=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((own_ip, own_port))
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.window_size = window_size
        self.own_port = own_port
        self.own_ip = own_ip
        self.filename = filename
        self.unacked = {}
        self.to_send = {}
        self.amount_to_send = 0
        self.initial_SYN = initial_SYN
        self.stream_id = 0
        self.received = {}
        self.last_send = 0
        self.timeout = timeout
        self.connected = False


    # to be used by the server
    def listen(self):
        received = 0
        while True:
            data, addr = self.sock.recvfrom(1016)
            pkt = Packet(b"")
            pkt.unpack(data)
            self.handle(packet=pkt)

    def reassemble(self):
        f = open(self.filename, "wb+")
        lowest = min(self.received)
        highest = max(self.received)
        for i in range(lowest, highest):
            packet = self.received.get(i)
            if packet is not None:
                f.write(packet.data)
                self.received.pop(i)
            else:
                break
        f.close()

    def send_file(self):
        self.sock.setblocking(False)
        self.create_packets()
        self.send_syn()
        # recv the syn_ack
        sent = time()
        while not self.connected:
            while sent - time() < self.timeout:
                try:
                    data, addr = self.sock.recvfrom(1016)
                    pkt = Packet(b"")
                    pkt.unpack(data)
                    print("connected")
                    print(pkt.header.flags)
                    self.connected = True
                    self.handle(packet=pkt)
                    break
                except:
                    pass
            if self.connected:
                break
            self.send_syn()
        self.create_packets()
        # send files as long as our
        while self.to_send or self.unacked:
            self.send_window(len(self.unacked))
            while time() - self.last_send < self.timeout:
                try:
                    data, addr = self.sock.recvfrom(1016)
                    pkt = Packet(b"")
                    pkt.unpack(data)
                    self.handle(packet=pkt)
                except:
                    pass
        self.send_fin()
        while self.connected:
            data, addr = self.sock.recvfrom(1016)
            pkt = Packet(b"")
            pkt.unpack(data)
            self.handle(pkt)

    # send_window to be used by the client
    def send_window(self, amount_to_resend):
        # we send one window
        if not self.to_send:
            return
        lowest_val = min(self.to_send)
        for i in range(lowest_val, lowest_val + self.window_size - amount_to_resend):
            pkt = self.to_send.get(i)
            if pkt is None:
                break
            print("len of to_send" + str(len(self.to_send)))
            print("len of unacked" + str(len(self.unacked)))
            pkt.header.SYN_number = self.initial_SYN + i
            pkt.header.windows = self.window_size
            pkt.header.stream_id = self.stream_id
            pkt.header.genchecksum(pkt.data)
            self.send(pkt.pack())
            self.to_send.pop(i)
            self.unacked.update({i + self.initial_SYN: (pkt, time())})

    def create_packets(self):
        f = open(self.filename, "rb")
        amount_of_packets = 1
        try:
            while True:
                data = f.read(1000)
                if data == b"":
                    break
                packet = Packet(data=data)
                packet.header.data_length = len(data)
                self.to_send.update({amount_of_packets: packet})
                amount_of_packets += 1
        finally:
            f.close()

    def handle(self, packet: Packet):
        if packet.header.is_synack():
            # we make sure the ack has the correct ACK number with a hacky solution
            packet.header.SYN_number = packet.header.ACK_number -1
            self.send_ack(packet)
            return

        if packet.is_syn():
            self.stream_id = packet.header.stream_id
            self.send_syn_ack(packet)
            return

        if packet.is_ack():
            print(self.unacked.items())
            self.unacked.pop(packet.header.ACK_number - 1)
            print("got ack for SYN: " + str(packet.header.SYN_number))
            return

        if packet.header.is_finack():
            self.connected = False
            self.send_ack(packet)
            return

        if packet.is_fin():
            self.connected = False
            self.send_fin_ack(packet)
            return

        # packet is a normal packet
        if packet.header.flags == 0:
            self.send_ack(packet)
            self.received.update({packet.header.SYN_number: packet})
            return

    # create and send the original SYN
    def send_syn(self):
        print("sending syn")
        packet = Packet(b"")
        packet.header.SYN_number = self.initial_SYN
        packet.header.flags = SYN
        packet.header.windows = self.window_size
        packet.header.stream_id = self.stream_id
        packet.header.data_length = 0
        packet.header.genchecksum(packet.data)
        self.send(packet.pack())
        self.unacked.update({packet.header.SYN_number: (packet, time())})

    # create and send the syn_ack
    def send_syn_ack(self, packet: Packet):
        print("sending syn ack")
        tosend = Packet(b"")
        tosend.header.ACK_number = packet.header.SYN_number + 1
        tosend.header.flags = SYNACK
        tosend.header.stream_id = random.randint(0, 65535)
        tosend.header.data_length = 0
        tosend.header.genchecksum(packet.data)
        self.send(tosend.pack())
        tosend.header.SYN_number = packet.header.ACK_number
        self.unacked.update({tosend.header.SYN_number: (tosend, time())})

    # send an ack message
    def send_ack(self, packet: Packet):
        tosend = Packet(b"")
        tosend.header.ACK_number = packet.header.SYN_number + 1
        tosend.header.flags = ACK
        tosend.header.stream_id = packet.header.stream_id
        tosend.header.data_length = 0
        tosend.header.genchecksum(packet.data)
        self.send(tosend.pack())

    def send_fin(self):
        print("sending fin")
        fin = Packet(b"")
        fin.header.SYN_number = self.initial_SYN + self.amount_to_send + 1
        fin.header.flags = FIN
        fin.header.stream_id = self.stream_id
        fin.header.windows = self.window_size
        fin.header.genchecksum(fin.data)
        self.send(fin.pack())
        self.unacked.update({fin.header.SYN_number: (fin, time())})

    def send_fin_ack(self, fin: Packet):
        print("sending fin_ack")
        self.reassemble()
        finack = Packet(b"")
        finack.header.SYN_number = fin.header.SYN_number + 1
        finack.header.ACK_number = fin.header.SYN_number + 1
        finack.header.flags = FINACK
        finack.header.windows = self.window_size
        finack.header.genchecksum(finack.data)
        self.send(finack.pack())
        self.unacked.update({finack.header.SYN_number:(fin, time())})
        self.reassemble()


    def send(self, msg: bytes):
        self.sock.sendto(msg, (self.dest_ip, self.dest_port))
