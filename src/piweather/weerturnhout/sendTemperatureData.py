import sys, os
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from piweather.sensors import read_ds18b20, read_dht22

def send_readings(T1,T2,T3,Tsurf,RH):
	print('-'*50)
	print('Sending data to server ...')
	url = "https://www.weerturnhout.be/php_scripts/upload_data_merksplas.php?T1={}&T2={}&T3={}&RH={}&Tsurf={}".format(T1,T2,T3,RH,Tsurf)
	print('URL used: {}'.format(url))
	r = requests.post(url)
	print('Done!')
	print('-'*50)

def main():
	"""
	This script takes temperature and pressure measurements from BMP180 sensor and uploads the data to a server using HTTP
	"""
	#sensors = read_ds18b20.get_sensors()
	#print(sensors)
	T1=float(read_ds18b20.get_temperature('/sys/bus/w1/devices/28-00000a4139e9/w1_slave'))
	T2=float(read_ds18b20.get_temperature('/sys/bus/w1/devices/28-00000a4142d3/w1_slave'))
	T3=float(read_ds18b20.get_temperature('/sys/bus/w1/devices/28-00000a411262/w1_slave'))
	Tsurf=float(read_ds18b20.get_temperature('/sys/bus/w1/devices/28-00000a9b37f5/w1_slave'))

	# Get current readings in nice format for debugging on screen
	#read_bmp180.get_reading()

	# Get the current readings as data
	#(T, P) = read_bmp180.get_data()

	# Get curent RH readings in nice format for debugging on screen
	read_dht22.main()

	# Get the current RH readings as data
	(RH, T_RH) = read_dht22.get_reading()

	# Upload data to server
	send_readings(T1,T2,T3,Tsurf,RH)

if __name__ == "__main__":
	main()
