#! /usr/bin/env python3
#from pyftdi.ftdi import Ftdi
import pyftdi.serialext

#Ftdi.show_devices() # use this to obtain url

url = 'ftdi://ftdi:232:AQ00K76I/1'
baudrate = 115200

port = pyftdi.serialext.serial_for_url(url, baudrate=baudrate)

print(port)

while 1:
  data = port.read(1)
  if len(data):
    print(data.decode('utf-8'))
