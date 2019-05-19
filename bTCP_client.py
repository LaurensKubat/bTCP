from bTCP import *

winsize = 100
timeout = 10

client = bTCP(own_ip="localhost", own_port=6542, dest_ip="localhost", dest_port=6543,
                           window_size=winsize, timeout=timeout,)

to_send = "test data which is less than 1000 bytes".encode("utf-8")
client.send(to_send)
