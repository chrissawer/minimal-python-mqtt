from abc import abstractmethod
import logging

logger = logging.getLogger(__name__)

class MsgType:
    RESERVED    =  0
    CONNECT     =  1
    CONNACK     =  2
    PUBLISH     =  3
    PUBACK      =  4
    PUBREC      =  5
    PUBREL      =  6
    PUBCOMP     =  7
    SUBSCRIBE   =  8
    SUBACK      =  9
    UNSUBSCRIBE = 10
    UNSUBACK    = 11
    PINGREQ     = 12
    PINGRESP    = 13
    DISCONNECT  = 14

class MqttMessageFactory:
    def getMqttMessage(self, flagsByte, msgBody):
        # Extract message type
        msgFlags = flagsByte & 0xf
        msgType = flagsByte >> 4

        if msgType == MsgType.PUBLISH:
            message = MqttPublish(msgFlags)
            message.setBody(msgBody)
            return message
        else:
            logger.warning(f'Unhandled message type {msgType}')
            raise Exception('Unhandled message type')

class MqttMessage():
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
        ms = MqttMessageSize()
        ms.setMessageSize(len(body))

        msg = b''
        msg += self.getTypeAndFlags()
        msg += ms.byteString
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
        body += len(self.protocol).to_bytes(2, 'big')
        body += self.protocol.encode('ascii')
        body += self.protocol_version.to_bytes(1, 'big')
        body += self.connect_flags.to_bytes(1, 'big')
        body += self.keepalive.to_bytes(2, 'big')
        body += len(self.client_id).to_bytes(2, 'big')
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
        body += self.message_identifier.to_bytes(2, 'big')
        body += len(self.topic).to_bytes(2, 'big')
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
        body += self.message_identifier.to_bytes(2, 'big')
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

class MqttDisconnect(MqttMessage):
    def __init__(self, msgFlags=0):
        super().__init__(MsgType.DISCONNECT, msgFlags)

    def getBody(self):
        return b''

    def setBody(self, body):
        raise NotImplementedError()

class MqttMessageSize():
    '''
    MQTT has an unusual multi-byte way of storing message sizes
    First bit of each byte indicates whether there are more bytes to read
    '''
    byteString = b''

    def addByte(self, nextByte):
        self.byteString += nextByte.to_bytes(1, 'big')

    def moreBytesNeeded(self):
        if self.byteString == b'':
            return true
        else:
            # Does the last byte have its top bit set?
            return (self.byteString[-1] & 0x80) == 0x80

    def getMessageSize(self):
        if len(self.byteString) < 1 or len(self.byteString) > 4:
            raise Exception('Byte list invalid length')

        size = 0
        topBitsCleared = [b & 0x7f for b in self.byteString]

        for i in range(4):
            if len(topBitsCleared) > i:
                size += topBitsCleared[i] << 7*i

        return size

    def setMessageSize(self, messageSize):
        if messageSize <= 0x7f: # 0111 1111
            self.byteString = messageSize.to_bytes(1, 'big')
        elif messageSize <= 0x3fff: # 0011 1111 1111 1111
            self.byteString = ((messageSize & 0x7f) | 0x80).to_bytes(1, 'big')
            self.byteString += ((messageSize & 0x3f80) >> 7).to_bytes(1, 'big')
        elif messageSize <= 0x1fffff: # 0001 1111 1111 1111 1111 1111
            self.byteString = ((messageSize & 0x7f) | 0x80).to_bytes(1, 'big')
            self.byteString += (((messageSize & 0x3f80) >> 7) | 0x80).to_bytes(1, 'big')
            self.byteString += ((messageSize & 0x1fc000) >> 14).to_bytes(1, 'big')
        elif messageSize <= 0xfffffff: # 0000 1111 1111 1111 1111 1111 1111 1111
            self.byteString = ((messageSize & 0x7f) | 0x80).to_bytes(1, 'big')
            self.byteString += (((messageSize & 0x3f80) >> 7) | 0x80).to_bytes(1, 'big')
            self.byteString += (((messageSize & 0x1fc000) >> 14) | 0x80).to_bytes(1, 'big')
            self.byteString += ((messageSize & 0xfe00000) >> 21).to_bytes(1, 'big')
        else:
            raise Exception('Message size too large')
