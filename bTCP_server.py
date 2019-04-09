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

    def __init__(self, port, ip, window, timeout, output):
        self.port = port
        self.ip = ip
        self.window = window
        self.timeout = timeout
        self.output = output
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock = sock
        self.sock.bind((server_ip, server_port))

    def listen(self):
        while True:
            packet = bTCP.packet.Packet()
            data, addr = self.sock.recvfrom(1016)
            packet.unpack(data)
            self.handle(packet)

    def handle(self, packet: bTCP.packet.Packet):
        ok = packet.validate()
        if not ok:
            self.sendNACK()
        elif packet.is_syn() and packet.is_ack():
            self.sendACK()
        elif packet.is_syn() and not packet.is_ack():
            self.sendSYNACK(packet)
        elif packet.is_ack():
            self.handleACK(packet)

    def handleACK(self, packet: bTCP.packet.Packet):

    def sendSYNACK(self, packet: bTCP.packet.Packet):

    def sendNACK(self, packet: bTCP.packet.Packet):

    def sendACK(self, packet: bTCP.packet.Packet):