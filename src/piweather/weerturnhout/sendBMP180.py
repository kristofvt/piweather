import sys, os
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from piweather.sensors import read_bmp180

def send_readings(T, P):
	print('-'*50)
	print('Sending data to server ...')
	url = "http://www.weerturnhout.be/php_scripts/upload_data_bmp180.php/?T_P='{}'&P='{}'".format(T, P)
	print('URL used: {}'.format(url))
	r = requests.post(url)
	print('Done!')
	print('-'*50)

def main():
	"""
	This script takes temperature and pressure measurements from BMP180 sensor and uploads the data to a server using HTTP
	"""

	# Get current readings in nice format for debugging on screen
	read_bmp180.get_reading()

	# Get the current readings as data
	(T, P) = read_bmp180.get_data()

	# Upload data to server
	send_readings(T, P)

if __name__ == "__main__":
	main()
