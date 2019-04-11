#!/usr/bin/env python3


import unittest
from bTCP.header import *
import binascii


class HeaderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.header = Header(1, 1, 1, 0, 0, 0)

    def tearDown(self) -> None:
        self.header = Header(1, 1, 1, 0, 0, 0)

    def test_checksum(self):
        checksum = self.header.genchecksum(self.header.serialize())
        self.assertEqual(checksum, binascii.crc32(self.header.serialize()), "header checksum is incorrect.")

    def test_serialize(self):
        serialized = self.header.serialize()
        correct = bytes(b'\x01\x01\x01\x00\x00\x00\x00')
        self.assertEqual(serialized, correct, "header is not serialized correct.")


if __name__ == '__main__':
    unittest.main()
