#!/usr/bin/env python3

import sys,os, glob
#import numpy as np
import datetime

def get_sensors(address='/sys/bus/w1/devices'):
	return glob.glob(os.path.join(address, '28*', 'w1_slave'))

def get_sensor_id(sensor):
	return os.path.basename(os.path.dirname(sensor))

def get_temperature(sensor):
	tfile = open(sensor)
	text = tfile.read()
	tfile.close()
	secondline = text.split("\n")[1]
	tdata = secondline.split(" ")[9]
	temperature = round(float(tdata[2:])/1000.,1)
	return(temperature)

def get_all_readings():
	print('-'*50)
	print('Looking for DS18B20 sensors ...')
	sensors = get_sensors()
	print('Found {} sensor(s):'.format(len(sensors)))
	print('Readings on {}:'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
	if len(sensors) > 0:
		for sensor in sensors:
			print('Sensor {}: {} C'.format(get_sensor_id(sensor), 
							get_temperature(sensor)))

def main():

	# For debugging
	get_all_readings()

if __name__=="__main__":
   main()
