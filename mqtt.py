import json
import logging
import select
import socket

from mqtt_message import *

logger = logging.getLogger(__name__)

def recvAllBytes(cs, count):
    firstRecv = cs.recv(count)
    if len(firstRecv) == count:
        # Most of the time you get all the bytes the first time
        return firstRecv
    else:
        # Loop until we have what we need
        allBytes = [firstRecv]
        remainingBytes = count - len(firstRecv)
        while remainingBytes > 0:
            nextBytes = cs.recv(remainingBytes)
            allBytes.append(nextBytes)
            remainingBytes -= len(nextBytes)
        return b''.join(allBytes)

def main(ipAddr, port, topicFilter, messageCallback):
    cs = socket.socket()
    cs.connect((ipAddr, port))

    cs.send(MqttConnect().getBytes())
    expectedResponse = MqttConnAck().getBytes()
    response = recvAllBytes(cs, len(expectedResponse))
    if response != expectedResponse:
        raise Exception('Didn\'t receive expected ConnAck')

    cs.send(MqttSubscribe().getBytes())
    expectedResponse = MqttSubAck().getBytes()
    response = recvAllBytes(cs, len(expectedResponse))
    if response != expectedResponse:
        raise Exception('Didn\'t receive expected SubAck')

    cs.setblocking(False)
    msgFactory = MqttMessageFactory()
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
                response = recvAllBytes(cs, len(expectedResponse))
                if response != expectedResponse:
                    raise Exception('Didn\'t receive expected PingResp')
            else:
                logger.warning('Ping timeout')

    cs.close()
