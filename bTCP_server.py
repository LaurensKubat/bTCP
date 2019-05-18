from bTCP.retry import *

winsize = 100
timeout = 10

server = bTCP(own_ip="localhost", own_port= 6543, filename="outputtest.txt", dest_ip="localhost",
                           dest_port=6542, window_size=winsize, timeout=timeout)

server.listen()