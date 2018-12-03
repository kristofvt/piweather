import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from piweather.sensors import read_bmp180

# Read BMP180
(T_bmp180, P_bmp180) = read_bmp180.get_data()
print('BMP180 Temperature = {} C'.format(T_bmp180))
print('BMP180 Air pressure = {} hPa'.format(P_bmp180))
