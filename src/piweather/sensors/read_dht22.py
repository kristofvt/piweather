#!/usr/bin/python

# DHT-22 humidity and temperature sensor
# Requires Adafruit_Python_DHT library to be installed!
# Script assumes sensor datapin to be attached to BCM17

import Adafruit_DHT
import datetime
import numpy as np

def get_reading():
	humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 17)
	return humidity, temperature

def main():
	# For debugging
	rh, t = get_reading()
	print('-'*50)
	print('Readings on {} for DHT-22'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
	print('RH = {}%'.format(np.round(rh,1)))
	print('Temperature = {} C'.format(np.round(t, 1)))

if __name__=="__main__":
	main()
