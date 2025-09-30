import json
import logging
import select
import socket
import time

from mqtt_message import *

logger = logging.getLogger(__name__)

def recvAllBytes(cs, count):
    firstRecv = cs.recv(count)
    if len(firstRecv) == count:
        # Most of the time you get all the bytes the first time
        return firstRecv
    else:
        # Loop until we have what we need
        logger.info('Didn\'t get all bytes')
        allBytes = [firstRecv]
        remainingBytes = count - len(firstRecv)
        while remainingBytes > 0:
            logger.info(f'Waiting for {remainingBytes} more bytes')
            try:
                nextBytes = cs.recv(remainingBytes)
                allBytes.append(nextBytes)
                remainingBytes -= len(nextBytes)
            except OSError: #BlockingIOError:
                logger.info('Sleeping while waiting for more bytes')
                time.sleep(0.001)
        logger.info(f'Got all {count} bytes')
        return b''.join(allBytes)

def mqttConnect(cs):
    cs.send(MqttConnect().getBytes())
    expectedResponse = MqttConnAck().getBytes()
    response = recvAllBytes(cs, len(expectedResponse))
    if response != expectedResponse:
        raise Exception('Didn\'t receive expected ConnAck')

def mqttSubscribe(cs):
    cs.send(MqttSubscribe().getBytes())
    expectedResponse = MqttSubAck().getBytes()
    response = recvAllBytes(cs, len(expectedResponse))
    if response != expectedResponse:
        raise Exception('Didn\'t receive expected SubAck')

def mqttPing(cs, selectProvider):
    cs.send(MqttPingReq().getBytes())
    expectedResponse = MqttPingResp().getBytes()
    ready = selectProvider.select([cs], [], [], 5)
    if ready[0]:
        response = recvAllBytes(cs, len(expectedResponse))
        if response != expectedResponse:
            raise Exception('Didn\'t receive expected PingResp')
    else:
        logger.warning('Ping timeout')

def main(ipAddr, port, topicFilter, messageCallback):
    cs = socket.socket()
    cs.connect((ipAddr, port))

    mqttConnect(cs)
    mqttSubscribe(cs)

    cs.setblocking(False)
    while True:
        ready = select.select([cs], [], [], 30)
        if ready[0]:
            (flagsByte, startOfSize) = recvAllBytes(cs, 2)

            msgSize = MqttMessageSize()
            msgSize.addByte(startOfSize)
            while msgSize.moreBytesNeeded():
                nextByte = recvAllBytes(cs, 1)[0]
                msgSize.addByte(nextByte)

            msgBody = recvAllBytes(cs, msgSize.getMessageSize())
            msg = MsgType.getMqttMessage(flagsByte, msgBody)
            logger.info(f'Received {msg.topic=} {msg.message=}')
            if msg.topic.endswith(topicFilter):
                messageCallback(json.loads(msg.message))
        else:
            logger.info('Sending ping')
            mqttPing(cs, select)

    cs.close()
