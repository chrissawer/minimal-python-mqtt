#!/usr/bin/env python3

import unittest
from unittest.mock import ANY
from unittest.mock import Mock

from mqtt import *

# python3 -m unittest mqtt_tests

class TestMqttConnect(unittest.TestCase):
    def test_mqtt_connect_happy_path(self):
        expectedRequest = MqttConnect().getBytes()
        correctResponse = MqttConnAck().getBytes()
        cs = Mock(**{'recv.return_value': correctResponse})

        mqttConnect(cs)
        cs.send.assert_called_once_with(expectedRequest)
        cs.recv.assert_called_once_with(len(correctResponse))

    def test_mqtt_connect_incorrect_response(self):
        cs = Mock(**{'recv.return_value': b'XXXX'})
        with self.assertRaises(Exception):
            mqttConnect(cs)

class TestMqttSubscribe(unittest.TestCase):
    def test_mqtt_subscribe_happy_path(self):
        expectedRequest = MqttSubscribe().getBytes()
        correctResponse = MqttSubAck().getBytes()
        cs = Mock(**{'recv.return_value': correctResponse})

        mqttSubscribe(cs)
        cs.send.assert_called_once_with(expectedRequest)
        cs.recv.assert_called_once_with(len(correctResponse))

    def test_mqtt_subscribe_incorrect_response(self):
        cs = Mock(**{'recv.return_value': b'XXXXX'})
        with self.assertRaises(Exception):
            mqttSubscribe(cs)

class TestMqttPing(unittest.TestCase):
    def test_mqtt_ping_happy_path(self):
        expectedRequest = MqttPingReq().getBytes()
        correctResponse = MqttPingResp().getBytes()
        cs = Mock(**{'recv.return_value': correctResponse})
        select = Mock(**{'select.return_value': [cs]})

        mqttPing(cs, select)
        cs.send.assert_called_once_with(expectedRequest)
        cs.recv.assert_called_once_with(len(correctResponse))
        select.select.assert_called_once_with(ANY, ANY, ANY, 5)

    def test_mqtt_ping_incorrect_response(self):
        cs = Mock(**{'recv.return_value': b'XX'})
        select = Mock(**{'select.return_value': ([cs], [], [])})
        with self.assertRaises(Exception):
            mqttPing(cs)

    def test_mqtt_ping_timeout(self):
        correctResponse = MqttPingResp().getBytes()
        cs = Mock(**{'recv.return_value': correctResponse})
        select = Mock(**{'select.return_value': ([], [], [])})

        mqttPing(cs, select)
        cs.recv.assert_not_called()
        select.select.assert_called_once_with(ANY, ANY, ANY, 5)

if __name__ == '__main__':
    unittest.main()
