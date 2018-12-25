import sys, os
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from piweather.sensors import read_ds18b20

def send_readings(T1,T2,T3,T_RH,RH):
	print('-'*50)
	print('Sending data to server ...')
	url = "http://www.weerturnhout.be/php_scripts/upload_data_merksplas.php?T1={}&T2={}$T3={}&T_RH={}&RH={}".format(T1,T2,T3,T_RH,RH)
	print('URL used: {}'.format(url))
	r = requests.post(url)
	print('Done!')
	print('-'*50)

def main():
	"""
	This script takes temperature and pressure measurements from BMP180 sensor and uploads the data to a server using HTTP
	"""

  sensors = get_sensors()
  T1=get_temperature(sensors[0])
  T2=get_temperature(sensors[1])
  T3=get_temperature(sensors[2])

	# Get current readings in nice format for debugging on screen
	#read_bmp180.get_reading()

	# Get the current readings as data
	#(T, P) = read_bmp180.get_data()

	# Upload data to server
	send_readings(T1,T2,T3,-999,-999)

if __name__ == "__main__":
	main()
