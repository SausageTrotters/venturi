from sensirion_i2c_driver import LinuxI2cTransceiver

txrx = LinuxI2cTransceiver('/dev/i2c-1')
txrx.transceive(37,b'\x36\x03',None,0,0)

import smbus
import time
import math
import serial
import threading

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

scale_port = '/dev/ttyUSB0'
serport = serial.Serial(port=scale_port, baudrate=9600)
print("waiting for serial!")
time.sleep(2.0)
serport.reset_input_buffer()

weight = -9999.99

sexit = False
def scale_function():
	global weight
	while sexit == False :
		res = serport.read_until(b'\r\n')
		if len(res) == 18 :
			data = (res[5:13]).decode('utf-8').replace(" ","")
			weight = float(data)
		time.sleep(0.01)


thr = threading.Thread(target=scale_function)
thr.start()


bus0=smbus.SMBus(0)
bus1=smbus.SMBus(1)
address = 0x6c

res = txrx.transceive(37,None,9,0,0)
scale = int.from_bytes(res[2][6:8])

if scale == 0 :
	print("Bad scale factor")
	quit()

zero = int.from_bytes(res[2][0:2], signed = True) / scale

print("Scale factor: ", scale, " Zero: %.3f" %zero)

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
	total0 = 0
	total1 = 0
	tcount0 = 0
	tcount1 = 0

	total_pos_root = 0
	total_neg_root = 0
	total_weight = 0
	
	
	ptg=[] # points to go at the end of the sequence!
	ifurl = "https://eu-central-1-1.aws.cloud2.influxdata.com"
	iforg = "CageTechnologies"
	ifbucket = "CAGEID01"
	iftoken = "1nwbGi_IcNmMZwJVytR6AzwnN48PHslUT1orUKFHZA0qd4G-ig27LZ8e7ef-8QcWilLrcu0t8ekwPfNgYoqF-A=="

	print("Acquiring data (10s)")
	
	while time.time() < tend  :

		res = txrx.transceive(37,None,9,0,0)
		dif = round(int.from_bytes(res[2][0:2], signed=True) / scale - zero, 2)
		temp = round(int.from_bytes(res[2][3:5], signed=True) / 200.0,2)

		total0 += dif
		tcount0 += 1
		total1 += temp
		tcount1+= 1

		if dif < 0 :
			total_neg_root += math.sqrt(-dif)
		else :
			total_pos_root += math.sqrt(dif)

		total_weight += weight

		output = "venturi "
		output += "dif=%.3f" % dif
		output += ",temp=%.2f" %temp
		output += ",weight=%0.4f" %weight
		output += " " + str(int(time.time() * 1000))
		output += "\n"
		ptg.append(output) 
	
	av0 = total0 / tcount0
	av1 = total1 / tcount1
	av2 = total_neg_root / tcount0
	av3 = total_pos_root / tcount0
	av4 = total_weight / tcount0

	tdif = 0
	if done_first == False :
		done_first = True
	else:
		tdif = time.time() - last_time

	last_time = time.time()

	print("Dif: %.2f" %av0,"Temp: %.1f" %av1, "NSQRT: %.2f" %av2, "PSQRT: %.2f" %av3, "Weight: %.4f" %av4, "DTime: %.1f" %tdif)
#	print (tcount0, ", ", tcount1)
	
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

sexit=True
time.sleep(1)				
serport.close()				

