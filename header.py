import binascii

# Header represents the header of a bTCP package
class Header:

    def __init__(self, stream_id=0, SYN_number=0, ACK_number=0, flags=0, windows=0, data_length=0, checksum=0):
        self.stream_id = stream_id
        self.SYN_number = SYN_number,
        self.ACK_number = ACK_number
        self.flags = flags
        self.windows = windows
        self.data_length = data_length
        self.checksum = checksum

    # genchecksum generates the checksum of the Header object
    def genchecksum(self, header: bytearray):
        self.checksum = binascii.crc32(header)

    # serialize the Header object into a bytearray, bytes are returned to ensure that it works the same as
    # the example header in the given framework
    def serialize(self) -> bytes:
        header = bytearray()
        header.append(self.stream_id)
        header.append(self.SYN_number)
        header.append(self.ACK_number)
        header.append(self.flags)
        header.append(self.windows)
        header.append(self.data_length)
        header.append(self.checksum)
        return bytes(header)

    # deserialize bytes into the header object
    def deserialize(self, header: bytes):
        self.stream_id = header[0:3]
        self.SYN_number = header[4:6]
        self.ACK_number = header[6:8]
        self.flags = header[8]
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
