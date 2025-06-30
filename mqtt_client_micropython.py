import logging
import network
import time

from mqtt import main

logger = logging.getLogger(__name__)

WIFI_SSID = ''
WIFI_PASSWORD = ''
MQTT_HOST = ''

def cli_callback(sensorMessage):
    temp = sensorMessage['BME280']['Temperature']
    humidity = sensorMessage['BME280']['Humidity']
    print(f'Got data {temp=} {humidity=}')

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.WARNING)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    wait = 0
    status = wlan.status()
    while wait < 10 and status != network.STAT_GOT_IP:
        logger.info(f'Connecting, current {status=}')
        time.sleep(1)
        wait += 1
        status = wlan.status()

    if status != network.STAT_GOT_IP:
        raise RuntimeError(f'Network connection failed, {status=}')
    else:
        status = wlan.ifconfig()
        logger.info('Connected, IP = ' + status[0])
        main(MQTT_HOST, 1883, '/SENSOR', cli_callback)
