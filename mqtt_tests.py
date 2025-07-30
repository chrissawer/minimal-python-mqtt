#!/usr/bin/env python3

import unittest
from unittest.mock import Mock

from mqtt import *

# python3 -m unittest mqtt_tests

class TestMqttConnect(unittest.TestCase):
    def test_mqtt_connect_happy_path(self):
        expectedRequest = MqttConnect().getBytes()
        correctResponse = MqttConnAck().getBytes()
        cs = Mock(**{'recv.return_value': correctResponse})

        mqttConnect(cs)
        cs.send.assert_called_with(expectedRequest)
        cs.recv.assert_called_with(len(correctResponse))

    def test_mqtt_connect_incorrect_response(self):
        incorrectResponse = b'1234'
        cs = Mock(**{'recv.return_value': incorrectResponse})
        with self.assertRaises(Exception):
            mqttConnect(cs)

class TestMqttSubscribe(unittest.TestCase):
    def test_mqtt_subscribe_happy_path(self):
        expectedRequest = MqttSubscribe().getBytes()
        correctResponse = MqttSubAck().getBytes()
        cs = Mock(**{'recv.return_value': correctResponse})

        mqttSubscribe(cs)
        cs.send.assert_called_with(expectedRequest)
        cs.recv.assert_called_with(len(correctResponse))

    def test_mqtt_subscribe_incorrect_response(self):
        incorrectResponse = b'12345'
        cs = Mock(**{'recv.return_value': incorrectResponse})
        with self.assertRaises(Exception):
            mqttSubscribe(cs)

if __name__ == '__main__':
    unittest.main()
