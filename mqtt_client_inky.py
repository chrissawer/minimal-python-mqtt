import logging

from font_fredoka_one import FredokaOne
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw

from mqtt import main

logger = logging.getLogger(__name__)

def cli_callback(sensorMessage):
    temp = sensorMessage['BME280']['Temperature']
    humidity = sensorMessage['BME280']['Humidity']

    img = Image.new('P', (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(FredokaOne, 22)
    draw.text((0, 25), 'Temperature:', inky_display.YELLOW, font)
    draw.text((150, 25), f'{temp}°', inky_display.BLACK, font)
    draw.text((0, 50), 'Humidity:', inky_display.YELLOW, font)
    draw.text((150, 50), f'{humidity:.0f}%', inky_display.BLACK, font)

    inky_display.set_image(img)
    inky_display.show()

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.WARNING)

    inky_display = InkyPHAT('yellow')
    inky_display.set_border(inky_display.WHITE)
    main('192.168.8.108', 1883, '/SENSOR', cli_callback)
