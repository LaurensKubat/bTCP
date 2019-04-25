#!/usr/bin/env python3


import unittest
from bTCP.packet import *
from bTCP.header import *


class PacketTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.packet = Packet(header=Header(1, 1, 1, 0, 0, 0), data=bytes(1000))
        self.packed = self.packet.pack()

    def tearDown(self) -> None:
        self.packet = None

    def test_validate(self):
        ok = self.packet.validate()
        self.assertTrue(ok)

    def test_unpack(self):
        packed = Packet(header=Header(1, 1, 1, 0, 0, 0))
        pack = Packet
        pack.unpack(pack=packed)
        self.assertTrue(pack.validate())

    def test_pack(self):
        packed = self.packet.pack()
        self.assertEqual(packed, self.packed)