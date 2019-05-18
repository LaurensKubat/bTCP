from threading import Thread
from queue import Queue, Empty
import socket
from bTCP import packet, header
import time
import random
# bTCP is network layer


class bTCP(object):
    def __init__(self, own_ip: str, own_port: int, dest_ip: str, dest_port: int, window_size: int, timeout: int):
        # the send buf contains raw bytes
        self.send_buf = Queue(window_size)
        # the receive buf contains packet.Packets
        self.recv_buf = Queue(window_size)
        self.conn = Conn(own_ip, own_port, dest_ip, dest_port)
        self.cur_stream_id = 0
        self.connected = False
        self.window_size = window_size
        self.timeout = timeout
        self.original_syn = 0
        self.sent = {}

    def handle(self, pkt:packet.Packet):
        # handle a SYN packet
        if pkt.header.flags == header.SYN:
            syn_ack = packet.Packet(data=b"", header=header.Header(
                ack_number=pkt.header.SYN_number + 1, flags=header.SYNACK, stream_id=random.randint(0, 65535)
            ))
            if pkt.header.windows > self.window_size:
                syn_ack.header.windows = self.window_size
            else:
                syn_ack.header.windows = pkt.header.windows
                self.window_size = pkt.header.windows
            syn_ack.header.genchecksum(syn_ack.data)
            self.send_buf.put(syn_ack, timeout=self.timeout)
            self.sent.update({syn_ack.header.ACK_number - 1: syn_ack})
            self.cur_stream_id = syn_ack.header.stream_id

        # handle a SYN ACK
        elif pkt.header.flags == header.SYNACK:
            ack = packet.Packet(data=b"", header=header.Header(
                ack_number=pkt.header.SYN_number + 1, flags=header.ACK, windows=self.window_size,
                stream_id=self.cur_stream_id,
            ))
            ack.header.genchecksum(ack.data)
            self.send_buf.put(ack, timeout=self.timeout)
            self.sent.update({ack.header.ACK_number - 1: ack})

        elif pkt.header.flags == header.ACK:

        elif pkt.header.flags == header.FIN:

        elif pkt.header.flags == header.FINACK:

        else:


    def send(self, data: bytes):
        self.opening_handshake(1)

    def opening_handshake(self, syn_number) -> bool:
        syn = packet.Packet(data=b"", header=header.Header(flags=header.SYN, windows=self.window_size,
                                                           syn_number=syn_number))
        syn.header.genchecksum(syn.data)
        self.send_buf.put(syn, timeout=self.timeout)
        sent = time.time()
        while not self.connected:
            try:
                syn_ack = self.send_buf.get(timeout=self.timeout)
                self.cur_stream_id = syn_ack.stream_id
                ack = packet.Packet(data=b"",
                                    header=header.Header(
                                        stream_id=syn_ack.header.stream_id, ack_number=syn_ack.header.ACK_number,
                                        flags=header.ACK, windows=syn_ack.header.windows)
                                    )
                self.send_buf.put(ack)
                self.original_syn = ack.header.ACK_number
                self.window_size = syn_ack.header.windows
                self.connected = True
            except Empty:
                pass
            if time.time() - sent >= self.timeout:
                self.send_buf.put(syn, timeout=self.timeout)
        return True


class Conn(Thread):

    def __init__(self, own_ip: str, own_port: int, dest_ip: str, dest_port: int, recv_buf: Queue, send_buf: Queue):
        Thread.__init__(self)
        self.ip = own_ip
        self.port = own_port
        self.dest_ip = dest_ip
        self.dest_port = dest_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((own_ip, own_port))
        self.recv_buf = recv_buf
        self.send_buf = send_buf

    def run(self) -> None:
        while True:
            data, addr = self.socket.recvfrom(1016)
            pkt = packet.Packet(b"")
            pkt.unpack(data)
            if not pkt.validate():
                continue
            self.recv_buf.put(pkt)
            if self.send_buf.qsize() > 0:
                pkt = self.send_buf.get()
                self.socket.sendto(pkt, (self.dest_ip, self.dest_port))



