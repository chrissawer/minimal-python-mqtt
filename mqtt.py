#!/usr/bin/env python

from abc import ABC, abstractmethod
from enum import IntEnum
import json
import logging
import select
import socket

logger = logging.getLogger(__name__)

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

class MqttMessageFactory:
    def getMqttMessage(self, flagsByte, msgBody):
        # Extract message type
        msgFlags = flagsByte & 0xf
        msgType = flagsByte >> 4

        match msgType:
            case MsgType.PUBLISH:
                message = MqttPublish(msgFlags)
                message.setBody(msgBody)
                return message
            case _:
                raise Exception('Unhandled message type')

class MqttMessage(ABC):
    protocol = 'MQTT'
    protocol_version = 4 # v3.1.1

    @abstractmethod
    def __init__(self, msgType, msgFlags):
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
        return tf.to_bytes(1, 'big')

    def getBytes(self):
        body = self.getBody()

        msg = b''
        msg += self.getTypeAndFlags()
        msg += len(body).to_bytes(1, 'big')
        msg += body
        return msg

class MqttConnect(MqttMessage):
    keepalive = 60 # seconds
    connect_flags = 0x2 # Clean Session Flag
    client_id = ''

    def __init__(self, msgFlags=0):
        super().__init__(MsgType.CONNECT, msgFlags)

    def getBody(self):
        body = b''
        body += len(self.protocol).to_bytes(2,'big')
        body += self.protocol.encode('ascii')
        body += self.protocol_version.to_bytes(1, 'big')
        body += self.connect_flags.to_bytes(1, 'big')
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
    def __init__(self, msgFlags=0):
        super().__init__(MsgType.CONNACK, msgFlags)

    def getBody(self):
        return b'\x00\x00'

    def setBody(self, body):
        raise NotImplementedError()

class MqttSubscribe(MqttMessage):
    message_identifier = 1
    topic = '#'
    qos = 0

    def __init__(self, msgFlags=2):
        super().__init__(MsgType.SUBSCRIBE, msgFlags)

    def getBody(self):
        body = b''
        body += self.message_identifier.to_bytes(2,'big')
        body += len(self.topic).to_bytes(2,'big')
        body += self.topic.encode('ascii')
        body += self.qos.to_bytes(1, 'big')
        return body

    def setBody(self, body):
        raise NotImplementedError()

class MqttSubAck(MqttMessage):
    message_identifier = 1
    qos = 0

    def __init__(self, msgFlags=0):
        super().__init__(MsgType.SUBACK, msgFlags)

    def getBody(self):
        body = b''
        body += self.message_identifier.to_bytes(2,'big')
        body += self.qos.to_bytes(1, 'big')
        return body

    def setBody(self, body):
        raise NotImplementedError()

class MqttPingReq(MqttMessage):
    def __init__(self, msgFlags=0):
        super().__init__(MsgType.PINGREQ, msgFlags)

    def getBody(self):
        return b''

    def setBody(self, body):
        raise NotImplementedError()

class MqttPingResp(MqttMessage):
    def __init__(self, msgFlags=0):
        super().__init__(MsgType.PINGRESP, msgFlags)

    def getBody(self):
        return b''

    def setBody(self, body):
        raise NotImplementedError()

class MqttPublish(MqttMessage):
    def __init__(self, msgFlags=0):
        super().__init__(MsgType.PUBLISH, msgFlags)

    def getBody(self):
        raise NotImplementedError()

    def setBody(self, body):
        topicLen = int.from_bytes(body[:2],'big')
        self.topic = body[2:topicLen+2].decode('ascii')
        self.message = body[topicLen+2:].decode('ascii')

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


def main(ipAddr, port, topicFilter, messageCallback):
    cs = socket.socket()
    cs.connect((ipAddr, port))

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

    cs.setblocking(False)
    msgFactory = MqttMessageFactory()
    while True:
        ready = select.select([cs], [], [], 30)
        if ready[0]:
            twoBytes = cs.recv(2)

            msgSize = MqttMessageSize(twoBytes[1])
            while msgSize.moreBytesNeeded():
                nextByte = cs.recv(1)[0]
                msgSize.addByte(nextByte)

            msgBody = cs.recv(msgSize.getMessageSize())
            flagsByte = twoBytes[0]
            msg = msgFactory.getMqttMessage(flagsByte, msgBody)
            logger.info(f'Received {msg.topic=} {msg.message=}')
            if msg.topic.endswith(topicFilter):
                messageCallback(json.loads(msg.message))
        else:
            logger.info('Sending ping')
            cs.send(MqttPingReq().getBytes())
            expectedResponse = MqttPingResp().getBytes()
            ready = select.select([cs], [], [], 5)
            if ready[0]:
                response = cs.recv(len(expectedResponse))
                if response != expectedResponse:
                    raise Exception('Didn\'t receive expected PingResp')
            else:
                logger.warning('Ping timeout')

    cs.close()
