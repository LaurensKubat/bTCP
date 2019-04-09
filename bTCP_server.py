import socket, argparse
import bTCP.packet

# Handle arguments
parser = argparse.ArgumentParser()
parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
parser.add_argument("-o","--output", help="Where to store file", default="tmp.file")
args = parser.parse_args()

server_ip = "127.0.0.1"
server_port = 9001

# Define a header format
header_format = "I"


# Server is the server
class Server:

    def __init__(self, port, ip, window, timeout, output, cons:dict):
        self.port = port
        self.ip = ip
        self.window = window
        self.timeout = timeout
        self.output = output
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock = sock
        self.sock.bind((server_ip, server_port))
        # cons is a dict containing dicts for each connection. The second level dictionary contains
        # WINDOW SIZE amount of packages
        self.cons = cons

    def listen(self):
        while True:
            packet = bTCP.packet.Packet()
            data, addr = self.sock.recvfrom(1016)
            packet.unpack(data)
            self.handle(packet)

    # handle the packet based on the flags of the header packet
    # TODO add handling of FIN, ADD a conn to the cons dict if msg is SYN. Add to correct conn dict
    def handle(self, packet: bTCP.packet.Packet):
        ok = packet.validate()
        if not ok:
            self.sendNACK(packet)
        elif packet.is_syn() and packet.is_ack():
            self.sendACK(packet)
        elif packet.is_syn() and not packet.is_ack():
            self.sendSYNACK(packet)
            self.cons[packet.header.stream_id] = {packet.header.SYN_number : packet}
        elif packet.is_ack():
            self.handleACK(packet)
        else:
            # if the connection isn't established yet, ignore the packet
            if packet.header.stream_id not in self.cons:
                return
            # add the packet to the correct window
            if packet.header.SYN_number not in self.cons[packet.header.stream_id]:
                self.cons[packet.header.stream_id].update({packet.header.SYN_number : packet})

    def handleACK(self, packet: bTCP.packet.Packet):


    def sendSYNACK(self, packet: bTCP.packet.Packet):

    def sendNACK(self, packet: bTCP.packet.Packet):

    def sendACK(self, packet: bTCP.packet.Packet):