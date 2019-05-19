import bTCP

class FTP(object):

    def __init__(self, own_ip: str, own_port: int, dest_ip: str, dest_port: int, winsize: int, timeout: int):
        self.bTCP = bTCP.bTCP(own_ip=own_ip, own_port=own_port, dest_port=dest_port, dest_ip=dest_ip,
                              window_size=winsize, timeout=timeout)

    def send_file(self, filename: str):
        f = open(filename, "rb")
        data = f.read()
        self.bTCP.send(data=data)

    def recv_file(self, filename: str):
        self.bTCP.listen()
        f = open(filename, "wb+")
        recv_data = b""
        for i in self.bTCP.received:
            recv_data += self.bTCP.received[i].data
        f.write(recv_data)
