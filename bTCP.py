from threading import Thread
from queue import Queue, Empty
import socket
from packet import *
import header
import time
import random


# bTCP is network layer
class bTCP(object):

    def __init__(self, own_ip: str, own_port: int, dest_ip: str, dest_port: int, window_size: int, timeout: int):
        # the send buf contains raw bytes
        self.send_buf = Queue(window_size)
        # the receive buf contains packet.Packets
        self.recv_buf = Queue(window_size)
        self.cur_stream_id = 0
        self.connected = False
        self.window_size = window_size
        self.timeout = timeout
        self.original_syn = 0
        self.sent = {}
        self.conn = Conn(own_ip, own_port, dest_ip, dest_port, recv_buf=self.recv_buf, send_buf=self.send_buf)
        self.conn.start()
        self.num_of_packets = 0
        self.received = []

    def listen(self, listentime):
        start = time.time()
        while time.time() - start < listentime:
            try:
                pkt = self.recv_buf.get(False)
                self.handle(pkt)
            except:
                pass
        self.conn.alive = False

    def handle(self, pkt: Packet):
        # handle a SYN packet
        if pkt.header.flags == SYN:
            print("received SYN")
            syn_ack = Packet(data=b"", header=header.Header(
                ack_number=pkt.header.SYN_number + 1, flags=header.SYNACK, stream_id=random.randint(0, 65535)
            ))
            if pkt.header.windows > self.window_size:
                syn_ack.header.windows = self.window_size
            else:
                syn_ack.header.windows = pkt.header.windows
                self.window_size = pkt.header.windows
            syn_ack.header.genchecksum(syn_ack.data)
            self.send_buf.put(syn_ack, timeout=self.timeout)
            self.cur_stream_id = syn_ack.header.stream_id
            self.connected = True
            print(self.connected)
            print(self.cur_stream_id)

        # if we recv a SYN ACK outside of our normal opening handshake, we ack it
        elif pkt.header.flags == SYNACK:
            ack = Packet(data=b"", header=header.Header(
                ack_number=pkt.header.SYN_number + 1, flags=header.ACK, windows=self.window_size,
                stream_id=self.cur_stream_id,
            ))
            ack.header.genchecksum(ack.data)
            self.send_buf.put(ack, timeout=self.timeout)

        elif pkt.header.flags == FIN:
            fin_ack = Packet(data=b"", header=header.Header(
                syn_number=pkt.header.SYN_number + 1, flags=header.FINACK, windows=self.window_size,
                ack_number=pkt.header.SYN_number, stream_id=self.cur_stream_id,))
            fin_ack.header.genchecksum(fin_ack.data)
            self.send_buf.put(fin_ack, timeout=self.timeout)
            print("sending finack")
            self.connected = False
            print("server connection:")
            print(self.connected)

        # if we recv a FINACK outside of our normal closing handshake, we ack it
        elif pkt.header.flags == FINACK:
            ack = Packet(data=b"",
                         header=header.Header(
                             stream_id=self.cur_stream_id, ack_number=pkt.header.SYN_number,
                             flags=ACK, windows=pkt.header.windows)
                         )
            ack.header.genchecksum(ack.data)
            self.send_buf.put(ack)

        elif pkt.header.flags == ACK:
            try:
                self.sent.pop(pkt.header.ACK_number - 1)
            except KeyError:
                print("keyError on ACK num" + str(pkt.header.ACK_number))
                pass

        else:
            ack = Packet(data=b"", header=header.Header(
                ack_number = pkt.header.SYN_number + 1, stream_id=self.cur_stream_id, windows=self.window_size,
                flags=ACK,
            ))
            self.received.append(pkt)
            ack.header.genchecksum(ack.data)
            self.send_buf.put(ack)

    def send(self, data: bytes):
        self.opening_handshake(1)
        packets = self.create_packets(data=data)
        self.send_packets(packets)
        self.closing_handshake()
        self.conn.alive = False

    def create_packets(self, data: bytes) -> [Packet]:
        needed_packets = len(data) // 1000 + 1
        print(needed_packets)
        packets = []
        while data:
            payload = data[:1000]
            data = data[1000:]
            pkt = Packet(data=payload, header=Header(data_length=len(payload)))
            packets.append(pkt)
        return packets

    def send_packets(self, packets: [Packet]):
        syn = self.original_syn + 1
        packets_sent = 0
        while packets_sent < len(packets) or len(self.sent) > 0:
            self.check_recv()
            resent = self.check_sent()
            # the second arg of the range ensures that we send all packets we are still allowed to send, while stayin
            # under the window size, we make use of the min function to ensure that we do not go out of bounds of
            # packets list
            largest = min(packets_sent + self.window_size - resent - len(self.sent), len(packets))
            for i in range(packets_sent, largest):
                self.check_recv()
                pkt = packets[i]
                print("starting to send")
                print(i)
                print(pkt)
                pkt.header.SYN_number = syn
                pkt.header.stream_id = self.cur_stream_id
                pkt.header.windows = self.window_size
                pkt.header.genchecksum(pkt.data)
                self.send_buf.put(pkt)
                self.sent.update({pkt.header.SYN_number: (pkt, time.time())})
                syn += 1
                self.num_of_packets += 1
                packets_sent += 1

    def check_recv(self):
        while self.recv_buf.qsize() != 0:
            try:
                pkt = self.recv_buf.get(False)
                self.handle(pkt=pkt)
            except Empty:
                pass

    def check_sent(self) -> int:
        resent = 0
        for syn in self.sent:
            buf = self.sent[syn]
            pkt, sent_time = buf
            if time.time() - sent_time > self.timeout:
                resent += 1
                self.send_buf.put(pkt)
                self.sent.update({pkt.header.SYN_number: (pkt, time.time())})
        return resent



    def opening_handshake(self, syn_number):
        syn = Packet(data=b"", header=header.Header(flags=header.SYN, windows=self.window_size,
                                                    syn_number=syn_number))
        syn.header.genchecksum(syn.data)
        self.send_buf.put(syn, timeout=self.timeout)
        self.original_syn = syn_number
        sent = time.time()
        print("sending syn and waiting for recv")
        while not self.connected:
            try:
                syn_ack = self.recv_buf.get(timeout=self.timeout)
                self.cur_stream_id = syn_ack.header.stream_id
                print(syn_ack.header.flags)
                print(syn_ack.header.SYN_number)
                print(syn_ack.header.ACK_number)
                ack = Packet(data=b"",
                                    header=header.Header(
                                        stream_id=syn_ack.header.stream_id, ack_number=syn_ack.header.ACK_number,
                                        flags=header.ACK, windows=syn_ack.header.windows)
                                    )
                ack.header.genchecksum(ack.data)
                self.send_buf.put(ack)
                self.window_size = syn_ack.header.windows
                self.connected = True
            except Empty:
                pass
            if time.time() - sent >= self.timeout:
                self.send_buf.put(syn, timeout=self.timeout)
            print(self.original_syn)
            print(self.connected)
        print("done opening handshake")
        return True

    def closing_handshake(self):
        fin = Packet(data=b"", header=header.Header(stream_id=self.cur_stream_id,
                                    syn_number=(self.original_syn + self.num_of_packets + 1), flags=FIN,
                                    windows=self.window_size))
        fin.header.genchecksum(fin.data)
        self.send_buf.put(fin)
        sent = time.time()
        print("sending fin")
        while self.connected:
            try:
                fin_ack = self.recv_buf.get(timeout=self.timeout)
                self.cur_stream_id = fin_ack.header.stream_id
                print(fin_ack.header.flags)
                print(fin_ack.header.SYN_number)
                print(fin_ack.header.ACK_number)
                ack = Packet(data=b"",
                             header=header.Header(
                                 stream_id=fin_ack.header.stream_id, ack_number=fin_ack.header.SYN_number,
                                 flags=header.ACK, windows=fin_ack.header.windows)
                             )
                ack.header.genchecksum(ack.data)
                self.send_buf.put(ack)
                self.connected = False
            except Empty:
                pass
            if time.time() - sent >= self.timeout:
                self.send_buf.put(fin, timeout=self.timeout)
        print("closing handshake done")
        print("connection: ")
        print(self.connected)


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
        self.alive = True
        self.socket.setblocking(False)

    def run(self) -> None:
        while self.alive:
            try:
                data, addr = self.socket.recvfrom(1016)
                pkt = Packet(b"")
                pkt.unpack(data)
                print("recv SYN: " + str(pkt.header.SYN_number))
                if not pkt.validate():
                    print("packet with the following flags was not validated")
                    print(pkt.header.flags)
                    continue
                self.recv_buf.put(pkt)
            except BlockingIOError:
                pass
            if self.send_buf.qsize() > 0:
                pkt = self.send_buf.get()
                print(pkt)
                print("sending packet SYN:" + str(pkt.header.SYN_number))
                print("flags are: " + str(pkt.header.flags))
                self.socket.sendto(pkt.pack(), (self.dest_ip, self.dest_port))



