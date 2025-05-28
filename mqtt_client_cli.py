from mqtt import *

def cli_callback(sensorMessage):
    temp = sensorMessage['BME280']['Temperature']
    humidity = sensorMessage['BME280']['Humidity']
    print(f'Got data {temp=} {humidity=}')

if __name__ == '__main__':
    main('192.168.8.108', 1883, '/SENSOR', cli_callback)
