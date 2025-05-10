#!/usr/bin/env python

from abc import ABC, abstractmethod
from enum import IntEnum
import socket

MsgType = IntEnum('MsgType', [
    'RESERVED',
    'CONNECT',
    'CONNACK',
    'PUBLISH',
    'PUBACK',
    'PUBREC',
    'PUBREL',
    'PUBCOMP',
    'SUBSCRIBE',
    'SUBACK',
    'UNSUBSCRIBE',
    'UNSUBACK',
    'PINGREQ',
    'PINGRESP',
    'DISCONNECT',
    ], start=0)

class MqttMessage(ABC):
    protocol = 'MQTT'
    protocol_version = 4 # v3.1.1

    @abstractmethod
    def __init__(self, msgType, msgFlags=0):
        self.msgType = msgType
        self.msgFlags = msgFlags

    @abstractmethod
    def getBody(self):
        return b''

    @abstractmethod
    def setBody(self, body):
        None

    def getTypeAndFlags(self):
        tf = (self.msgType << 4) | self.msgFlags
        return tf.to_bytes()

    def getBytes(self):
        body = self.getBody()

        msg = b''
        msg += self.getTypeAndFlags()
        msg += len(body).to_bytes()
        msg += body
        return msg

class MqttConnect(MqttMessage):
    keepalive = 60 # seconds
    connect_flags = 0x2 # Clean Session Flag
    client_id = ''

    def __init__(self):
        super().__init__(MsgType.CONNECT)

    def getBody(self):
        body = b''
        body += len(self.protocol).to_bytes(2,'big')
        body += self.protocol.encode('ascii')
        body += self.protocol_version.to_bytes()
        body += self.connect_flags.to_bytes()
        body += self.keepalive.to_bytes(2,'big')
        body += len(self.client_id).to_bytes(2,'big')
        return body

    def setBody(self, body):
        raise NotImplementedError()

class MqttConnAck(MqttMessage):
    '''
    Minimal implementation of connack
    Enough for a client to verify the server's connack
    '''
    def __init__(self):
        super().__init__(MsgType.CONNACK)

    def getBody(self):
        return b'\x00\x00'

    def setBody(self, body):
        raise NotImplementedError()

class MqttSubscribe(MqttMessage):
    message_identifier = 1
    topic = '#'
    qos = 0

    def __init__(self):
        super().__init__(MsgType.SUBSCRIBE, msgFlags=0x2)

    def getBody(self):
        body = b''
        body += self.message_identifier.to_bytes(2,'big')
        body += len(self.topic).to_bytes(2,'big')
        body += self.topic.encode('ascii')
        body += self.qos.to_bytes()
        return body

    def setBody(self, body):
        raise NotImplementedError()

class MqttSubAck(MqttMessage):
    message_identifier = 1
    qos = 0

    def __init__(self):
        super().__init__(MsgType.SUBACK)

    def getBody(self):
        body = b''
        body += self.message_identifier.to_bytes(2,'big')
        body += self.qos.to_bytes()
        return body

    def setBody(self, body):
        raise NotImplementedError()

class MqttPublish(MqttMessage):
    def __init__(self):
        super().__init__(MsgType.PUBLISH)

    def getBody(self):
        raise NotImplementedError()

    def setBody(self, body):
        raise NotImplementedError()

class MqttMessageSize():
    '''
    MQTT has an unusual multi-byte way of storing message sizes
    First bit of each byte indicates whether there are more bytes to read
    '''

    def __init__(self, firstByte):
        self.byteList = [firstByte]

    def addByte(self, nextByte):
        self.byteList.append(nextByte)

    def moreBytesNeeded(self):
        # Does the last byte have its top bit set?
        return (self.byteList[-1] & 0x80) == 0x80

    def getMessageSize(self):
        if len(self.byteList) < 1 or len(self.byteList) > 4:
            raise Exception('Byte list invalid length')

        size = 0
        topBitsCleared = [b & 0x7f for b in self.byteList]

        for i in range(4):
            if len(topBitsCleared) > i:
                size += topBitsCleared[i] << 7*i

        return size


if __name__ == '__main__':
    cs = socket.socket()
    cs.connect(('192.168.8.108', 1883))

    cs.send(MqttConnect().getBytes())
    expectedResponse = MqttConnAck().getBytes()
    response = cs.recv(len(expectedResponse))
    if response != expectedResponse:
        raise Exception('Didn\'t receive expected ConnAck')

    cs.send(MqttSubscribe().getBytes())
    expectedResponse = MqttSubAck().getBytes()
    response = cs.recv(len(expectedResponse))
    if response != expectedResponse:
        raise Exception('Didn\'t receive expected SubAck')

    while True:
        twoBytes = cs.recv(2)

        ms = MqttMessageSize(twoBytes[1])
        while ms.moreBytesNeeded():
            nextByte = cs.recv(1)[0]
            ms.addByte(nextByte)

        message = cs.recv(ms.getMessageSize())
        flags = twoBytes[0]
        # TODO move to appropriate place
        topicLen = int.from_bytes(message[:2],'big')
        topic = message[2:topicLen+2]
        restOfMessage = message[topicLen+2:]
        print(f'Received {flags=} {topicLen=} {topic=} {restOfMessage=}')

    cs.close()
