from bTCP.retry import *

winsize = 100
timeout = 10

client = bTCP(own_ip="localhost", own_port=6542, filename="test.txt", dest_ip="localhost", dest_port=6543,
                           window_size=winsize, timeout=timeout, initial_SYN=1)

client.send_file()