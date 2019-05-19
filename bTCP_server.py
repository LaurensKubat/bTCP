from bTCP import *

winsize = 100
timeout = 10

server = bTCP(own_ip="localhost", own_port= 6543, dest_ip="localhost",
                           dest_port=6542, window_size=winsize, timeout=timeout)

server.listen()
print("trying to reconstruct")
data = b""
print(len(server.received))
for i in server.received:
    data += server.received[i].data
print(data)
print(data.decode("utf-8"))
