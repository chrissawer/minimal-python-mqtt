#!/usr/bin/env python

import unittest

from mqtt_message import *

# python3 -m unittest mqtt_message_tests
# python3 -m unittest mqtt_message_tests.TestMqttMessage

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

    def test_pingreq(self):
        msg = MqttPingReq()
        msgBytes = msg.getBytes()

        self.assertEqual(2, len(msgBytes))
        self.assertEqual(b'\xc0', msgBytes[0:1]) # Type
        self.assertEqual(b'\x00', msgBytes[1:2]) # Length

    def test_pingresp(self):
        msg = MqttPingResp()
        msgBytes = msg.getBytes()

        self.assertEqual(2, len(msgBytes))
        self.assertEqual(b'\xd0', msgBytes[0:1]) # Type
        self.assertEqual(b'\x00', msgBytes[1:2]) # Length

class TestMqttMessageSize(unittest.TestCase):
    messageSizeMap = {
        0x78: b'\x78',
        0x3a8: b'\xa8\x07',
        0x123456: b'\xd6\xe8\x48',
        0xe5482e: b'\xae\x90\x95\x07',
    }

    def test_size_to_byte_string(self):
        for size, byteString in self.messageSizeMap.items():
            ms = MqttMessageSize()
            ms.setMessageSize(size)
            self.assertEqual(byteString, ms.byteString)

    def test_byte_string_to_size(self):
        for size in self.messageSizeMap.keys():
            firstByte = self.messageSizeMap[size][0]
            otherBytes = self.messageSizeMap[size][1:]
            ms = MqttMessageSize()
            ms.addByte(firstByte)
            for byte in otherBytes:
                self.assertTrue(ms.moreBytesNeeded())
                ms.addByte(byte)
            self.assertFalse(ms.moreBytesNeeded())
            self.assertEqual(size, ms.getMessageSize())

class TestMqttMessageFactory(unittest.TestCase):
    def test_publish(self):
        mf = MqttMessageFactory()
        msg = mf.getMqttMessage(0x31, b'\x00\x01AB')
        self.assertEqual(type(MqttPublish()), type(msg))
        self.assertEqual('A', msg.topic)
        self.assertEqual('B', msg.message)

if __name__ == '__main__':
    unittest.main()
