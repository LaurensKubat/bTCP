#!/usr/bin/env python3

import binascii
import struct


# Header represents the header of a bTCP package
class Header:

    # TODO make sure the size of all the values are correct
    def __init__(self, stream_id=0, syn_number=0, ack_number=0, flags=0, windows=0,
                 data_length=0, checksum=0):
        self.stream_id = stream_id
        self.SYN_number = syn_number
        self.ACK_number = ack_number
        self.flags = flags
        self.windows = windows
        self.data_length = data_length
        self.checksum = checksum

    # genchecksum generates the checksum of the Header object
    def genchecksum(self):
        header = struct.pack("IHHBBH", self.stream_id, self.SYN_number, self.ACK_number, self.flags,
                             self.windows, self.data_length, )
        self.checksum = binascii.crc32(header)

    # serialize the Header object into a bytearray, bytes are returned to ensure that it works the same as
    # the example header in the given framework
    def serialize(self) -> bytes:
        header = struct.pack("IHHBBHI", self.stream_id, self.SYN_number, self.ACK_number, self.flags,
                             self.windows, self.data_length, self.checksum)
        return bytes(header)

    # deserialize bytes into the header object
    def deserialize(self, header: bytes):
        self.stream_id = struct.unpack("I", header[0:4])[0]
        self.SYN_number = struct.unpack("H", header[4:6])[0]
        self.ACK_number = struct.unpack("H", header[6:8])[0]
        self.flags = header[8] # since one byte from bytes can be seen as an int, we do not unpack this
        self.windows = header[9]  # same as above
        self.data_length = struct.unpack("H", header[10:12])[0]
        self.checksum = struct.unpack("I", header[12:16])[0]

    # returns true or false depending on if the header is correct
    def validate(self) -> bool:
        header = struct.pack("IHHBBH", self.stream_id, self.SYN_number, self.ACK_number, self.flags,
                             self.windows, self.data_length,)
        checksum = binascii.crc32(header)
        return checksum == self.checksum

    # is_syn checks if the SYN flag is on by bitshifting all the other bits away (done for efficiency)
    # the first bit is SYN, second is ACK third is FIN
    def is_syn(self) -> bool:
        flag_buf = self.flags
        syn_flag = flag_buf << 7 & 255
        return bool(syn_flag)

    # is_ack checks if the ACK flag is set
    def is_ack(self) -> bool:
        flag_buf = self.flags
        flag_buf = flag_buf >> 1
        ack_flag = flag_buf << 7 & 255
        return bool(ack_flag)

    # is_fin checks if the FIN flag is set
    def is_fin(self) -> bool:
        flag_buf = self.flags
        flag_buf = flag_buf >> 2
        fin_flag = flag_buf << 7 & 255
        return bool(fin_flag)


def set_syn(flag: int) -> int:
    return flag | 1


def set_ack(flag: int) -> int:
    return flag | 2


def set_fin(flag: int) -> int:
    return flag | 4
