import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from piweather.sensors import read_bmp180, read_ds18b20

# Read BMP180
read_bmp180.get_reading()

# Read ds18b20
read_ds18b20.get_all_readings()
