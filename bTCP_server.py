import socket
import argparse
import bTCP.bTCP
import bTCP.packet

# Handle arguments
parser = argparse.ArgumentParser()
parser.add_argument("-w", "--window", help="Define bTCP window size", type=int, default=100)
parser.add_argument("-t", "--timeout", help="Define bTCP timeout in milliseconds", type=int, default=100)
parser.add_argument("-o", "--output", help="Where to store file", default="tmp.file")
args = parser.parse_args()

timeout = 100

server_ip = "127.0.0.1"
server_port = 9001

# Define a header format
header_format = "I"

SYNACK = 1
NORMAL = 2
FINACK = 3

# Server is the server, it inherits from bTCP, which implements basic bTCP functions
class Server(object):

    def __init__(self, baseTCP: bTCP.bTCP.BasebTCP):
        self.base = baseTCP



    # listen to the socket
    def listen(self):
        while True:
            packet = bTCP.packet.Packet()
            data, addr = self.base.sock.recvfrom(1016)
            packet.unpack(data)
            self.base.handle(packet)
            self.base.checksent()

    def reassemble(self, stream_id):
        cur_syn = self.base.cur_syn_numbers[stream_id]






