#!/usr/bin/env python

import unittest

from mqtt import *

# python3 -m unittest mqtt_tests
# python3 -m unittest mqtt_tests.TestMqttMessage

class TestMqttMessage(unittest.TestCase):
    def test_connect(self):
        msg = MqttConnect()
        msgBytes = msg.getBytes()

        self.assertEqual(14, len(msgBytes))
        self.assertEqual(b'\x10', msgBytes[0:1]) # Type
        self.assertEqual(b'\x0c', msgBytes[1:2]) # Length
        self.assertEqual(b'\x00\x04MQTT', msgBytes[2:8]) # Protocol name
        self.assertEqual(b'\x04', msgBytes[8:9]) # MQTT version
        self.assertEqual(b'\x02', msgBytes[9:10]) # Connect flags
        self.assertEqual(b'\x00\x3c', msgBytes[10:12]) # Keep alive
        self.assertEqual(b'\x00\x00', msgBytes[12:14]) # Client ID

    def test_connack(self):
        msg = MqttConnAck()
        msgBytes = msg.getBytes()

        self.assertEqual(4, len(msgBytes))
        self.assertEqual(b'\x20', msgBytes[0:1]) # Type
        self.assertEqual(b'\x02', msgBytes[1:2]) # Length
        self.assertEqual(b'\x00', msgBytes[2:3]) # Acknowledge flags
        self.assertEqual(b'\x00', msgBytes[3:4]) # Return code

    def test_subscribe(self):
        msg = MqttSubscribe()
        msgBytes = msg.getBytes()

        self.assertEqual(8, len(msgBytes))
        self.assertEqual(b'\x82', msgBytes[0:1]) # Type
        self.assertEqual(b'\x06', msgBytes[1:2]) # Length
        self.assertEqual(b'\x00\x01', msgBytes[2:4]) # Message identifier
        self.assertEqual(b'\x00\x01#', msgBytes[4:7]) # Topic
        self.assertEqual(b'\x00', msgBytes[7:8]) # QoS

    def test_suback(self):
        msg = MqttSubAck()
        msgBytes = msg.getBytes()

        self.assertEqual(5, len(msgBytes))
        self.assertEqual(b'\x90', msgBytes[0:1]) # Type
        self.assertEqual(b'\x03', msgBytes[1:2]) # Length
        self.assertEqual(b'\x00\x01', msgBytes[2:4]) # Message identifier
        self.assertEqual(b'\x00', msgBytes[4:5]) # QoS

class TestMqttMessageSize(unittest.TestCase):
    def test_single_byte(self):
        ms = MqttMessageSize(120)
        self.assertFalse(ms.moreBytesNeeded())
        self.assertEqual(120, ms.getMessageSize())

    def test_two_bytes(self):
        ms = MqttMessageSize(0xa8)
        self.assertTrue(ms.moreBytesNeeded())
        ms.addByte(0x07)
        self.assertFalse(ms.moreBytesNeeded())
        self.assertEqual(0x3a8, ms.getMessageSize())

    def test_four_bytes(self):
        ms = MqttMessageSize(0xae)
        self.assertTrue(ms.moreBytesNeeded())
        ms.addByte(0x90)
        self.assertTrue(ms.moreBytesNeeded())
        ms.addByte(0x95)
        self.assertTrue(ms.moreBytesNeeded())
        ms.addByte(0x07)
        self.assertFalse(ms.moreBytesNeeded())
        self.assertEqual(0xe5482e, ms.getMessageSize())
