from sensirion_i2c_driver import LinuxI2cTransceiver
import serial
import time
import threading

txrx = LinuxI2cTransceiver('/dev/i2c-1')
txrx.transceive(37,b'\x36\x03',None,0,0)

scale_port = '/dev/ttyUSB0'
serport = serial.Serial(port=scale_port, baudrate=9600)
print("waiting for serial!")
time.sleep(2.0)
serport.reset_input_buffer()

weight = -9999.99

def scale_function():
	global weight
	while True :
		res = serport.read_until(b'\r\n')
		if len(res) == 18 :
			data = (res[5:13]).decode('utf-8').replace(" ","")
			weight = float(data)
		time.sleep(0.01)


thr = threading.Thread(target=scale_function)
thr.start()

import smbus
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

bus0=smbus.SMBus(0)
bus1=smbus.SMBus(1)
address = 0x6c

exit = 0
offset0 = 0.0
offset1 = 0.0
done_first = False
last_time = 0

while exit == False :
	res = input("Acquire data (10s)? [Yn]")
	if res != "" and res!="Y" and res!="y" :
		break

	last0 = 0
	last1 = 0
	tend = 10.0 + time.time()
	rdcnt0 = 0
	rdcnt1 = 0
	rdcnt2 = 0
	total0 = 0
	total1 = 0
	total2 = 0
	tcount0 = 0
	tcount1 = 0
	tcount2 = 0
	
	
	ptg=[] # points to go at the end of the sequence!
	ifurl = "https://eu-central-1-1.aws.cloud2.influxdata.com"
	iforg = "CageTechnologies"
	ifbucket = "CAGEID01"
	iftoken = "1nwbGi_IcNmMZwJVytR6AzwnN48PHslUT1orUKFHZA0qd4G-ig27LZ8e7ef-8QcWilLrcu0t8ekwPfNgYoqF-A=="

	print("Acquiring data (10s)")
	
	while time.time() < tend  :

		res = txrx.transceive(37,None,9,0,0)
		dif = round(int.from_bytes(res[2][0:2], signed=True) / 60.0, 2)
		temp = round(int.from_bytes(res[2][3:5], signed=True) / 200.0,2)
		scale = int.from_bytes(res[2][6:8])

		total0 += dif
		tcount0 += 1
		total1 += temp
		tcount1 += 1
		total2 += weight
		tcount2 += 1

		output = "venturi dif="
		output += "%.2f" % dif
		output += ",temp=%.2f" %temp
		output += ",scale=%.0f" %scale
		output += ",weight=%.4f " %weight
		output += str(int(time.time() * 1000))
		output += "\n"
		ptg.append(output) 
	
	av0 = total0 / tcount0
	av1 = total1 / tcount1
	av2 = total2 / tcount2
	
	if done_first == False :
		delta = 0.0
		last_time = time.time()
		done_first = True
	else :
		delta = time.time() - last_time
		last_time = time.time()

	print("Raw: %.1f" %av0," ","%.3f" %av1, " ", "%.4f" %av2, "%.1f" %delta)
	print (tcount0, ", ", tcount1)
	
	res = input("Save data to influx? [Yn]")
	
	if res == "" or res=="Y" or res=="y" :
		print("Initialising InfluxDBClient")
		client = InfluxDBClient(url=ifurl, token=iftoken, org=iforg, enable_gzip=True, timeout=5_000)
		done = False
		while done == False :
			try :
				write_api = client.write_api(write_options=SYNCHRONOUS)
				print("Uploading....")
				write_api.write(bucket=ifbucket, org=iforg, record=ptg, write_precision=WritePrecision.MS)
				done = True
			except :
				res = input("Upload failed! - retry? [Yn]")
				if res == "" or res=="Y" or res=="y" :
					print("Retrying upload")
				else :
					done = True
					print ("Upload cancelled!")
				
