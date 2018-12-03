#!/usr/bin/env python3

import sys,os, glob

def get_sensors(address='/sys/bus/w1/devices'):
	return glob.glob(os.path.join(address, '28*', 'w1_slave'))


def main():

	sensors = get_sensors()
	print('Found following sensors:')
	for sensor in sensors: print(sensor)

if __name__=="__main__":
   main()
