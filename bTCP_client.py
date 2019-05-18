from bTCP import *

winsize = 100
timeout = 10

client = bTCP(own_ip="localhost", own_port=6542, dest_ip="localhost", dest_port=6543,
                           window_size=winsize, timeout=timeout,)

client.opening_handshake(1)
client.closing_handshake()
