import datetime
import logging

from mqtt import main

logger = logging.getLogger(__name__)

def cli_callback(sensorMessage):
    temp = sensorMessage['BME280']['Temperature']
    humidity = sensorMessage['BME280']['Humidity']
    print(datetime.datetime.now(), f'Got data {temp=} {humidity=}')

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.WARNING)
    main('192.168.8.108', 1883, '/SENSOR', cli_callback)
