#!/usr/bin/env python3


import unittest
from header import *
import binascii


class HeaderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.header = Header(1, 1, 1, 0, 0, 0)

    def tearDown(self) -> None:
        self.header = None

    def test_checksum(self):
        checksum = 917831061
        self.assertEqual(checksum, binascii.crc32(self.header.serialize()), "header checksum is incorrect.")

    def test_serialize(self):
        serialized = self.header.serialize()
        correct = bytes(b'\x01\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertEqual(serialized, correct, "header is not serialized correct.")

    def test_deserialize(self):
        ser = bytes(b'\x01\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        h = Header()
        h.deserialize(ser)
        self.assertEqual(h.stream_id, self.header.stream_id)
        self.assertEqual(h.checksum, self.header.checksum)
        self.assertEqual(h.data_length, self.header.data_length)
        self.assertEqual(h.flags, self.header.flags)
        self.assertEqual(h.ACK_number, self.header.ACK_number)
        self.assertEqual(h.SYN_number, self.header.SYN_number)
        self.assertEqual(h.windows, self.header.windows)

    def test_validate(self):
        self.assertFalse(self.header.validate())
        self.header.genchecksum()  # helper function
        self.assertTrue(self.header.validate())

    # for the testing of the flags, the initial header does not have any set flags, thus it should be false at
    # first and after setting a flag, only that specific flag should be true
    def test_syn_flag(self):
        self.assertFalse(self.header.is_syn())
        self.header.flags = set_syn(self.header.flags)
        self.assertTrue(self.header.is_syn())
        self.assertFalse(self.header.is_ack())
        self.assertFalse(self.header.is_fin())

    def test_ack_flag(self):
        self.assertFalse(self.header.is_ack())
        self.header.flags = set_ack(self.header.flags)
        self.assertTrue(self.header.is_ack())
        self.assertFalse(self.header.is_syn())
        self.assertFalse(self.header.is_fin())

    def test_fin_flag(self):
        self.assertFalse(self.header.is_fin())
        self.header.flags = set_fin(self.header.flags)
        self.assertTrue(self.header.is_fin())
        self.assertFalse(self.header.is_syn())
        self.assertFalse(self.header.is_ack())


if __name__ == '__main__':
    unittest.main()
