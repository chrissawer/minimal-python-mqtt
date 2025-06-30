#!/usr/bin/env python3

import datetime
import logging
import sys

from mqtt import main

logger = logging.getLogger(__name__)

def cli_callback(sensorMessage):
    temp = sensorMessage['BME280']['Temperature']
    humidity = sensorMessage['BME280']['Humidity']
    print(datetime.datetime.now(), f'Got data {temp=} {humidity=}')

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.WARNING)

    if len(sys.argv) < 2:
        logger.error('MQTT hostname not supplied')
    else:
        main(sys.argv[1], 1883, '/SENSOR', cli_callback)
