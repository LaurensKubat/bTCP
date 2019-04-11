#!/usr/bin/env python3

import binascii


# Header represents the header of a bTCP package
class Header:

    # TODO make sure the size of all the values are correct
    def __init__(self, stream_id=bytes(4), syn_number=bytes(2), ack_number=bytes(2), flags=bytes(1), windows=bytes(1),
                 data_length=(bytes(2)), checksum=bytes(4)):
        self.stream_id = stream_id
        self.SYN_number = syn_number
        self.ACK_number = ack_number
        self.flags = flags
        self.windows = windows
        self.data_length = data_length
        self.checksum = checksum

    # genchecksum generates the checksum of the Header object
    def genchecksum(self, header: bytes):
        self.checksum = binascii.crc32(header)

    # TODO improve serialization such that the header is processed correctly
    # serialize the Header object into a bytearray, bytes are returned to ensure that it works the same as
    # the example header in the given framework
    def serialize(self) -> bytes:
        header = bytearray()
        header.append(int(self.stream_id))
        header.append(int(self.SYN_number))
        header.append(int(self.ACK_number))
        header.append(int(self.flags))
        header.append(int(self.windows))
        header.append(int(self.data_length))
        header.append(int.from_bytes(self.checksum, byteorder='big'))
        return bytes(header)

    # deserialize bytes into the header object
    def deserialize(self, header: bytes):
        self.stream_id = header[0:3]
        self.SYN_number = header[4:6]
        self.ACK_number = header[6:8]
        self.flags = int(header[8])
        self.windows = header[9]
        self.data_length = header[10:12]
        self.checksum = header[12:16]

    # returns true or false depending on if the header is correct
    def validate(self) -> bool:
        checksumless = bytearray()
        checksumless.append(self.stream_id)
        checksumless.append(self.SYN_number)
        checksumless.append(self.ACK_number)
        checksumless.append(self.flags)
        checksumless.append(self.windows)
        checksumless.append(self.data_length)
        checksum = binascii.crc32(checksumless)
        return checksum == self.checksum

    # is_syn checks if the SYN flag is on by bitshifting all the other bits away (done for efficiency)
    # the first bit is SYN, second is ACK third is FIN
    def is_syn(self) -> bool:
        flagbuf = self.flags
        synflag = flagbuf << 7 & 255
        return bool(synflag)

    def is_ack(self) -> bool:
        flagbuf = self.flags
        flagbuf = flagbuf >> 1
        ackflag = flagbuf << 7 & 255
        return bool(ackflag)

    def is_fin(self) -> bool:
        flagbuf = self.flags
        flagbuf = flagbuf >> 2
        finflag = flagbuf << 7 & 255
        return bool(finflag)


def new_header(header: bytes) -> Header:
    buf = Header()
    buf.deserialize(header)
    return buf


def set_syn(flag: int) -> int:
    return flag | 1


def set_ack(flag: int) -> int:
    return flag | 2


def set_fin(flag: int) -> int:
    return flag | 4
