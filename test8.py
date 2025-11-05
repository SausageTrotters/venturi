from sensirion_i2c_driver import LinuxI2cTransceiver
import sys

txrx = LinuxI2cTransceiver('/dev/i2c-1')
txrx.transceive(37,b'\x36\x03',None,0,0)

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
acq_time = 10.0 	#default time

if(len(sys.argv) == 2) :
	acq_time = float(sys.argv[1])

while exit == False :

	res = input("Acquire data (%.1f)? [Yn]" %acq_time)
	if res != "" and res!="Y" and res!="y" :
		break

	last0 = 0
	last1 = 0
	rdcnt0 = 0
	rdcnt1 = 0
	total0 = 0
	total1 = 0
	tcount0 = 0
	tcount1 = 0
	
	
	ptg=[] # points to go at the end of the sequence!
	ifurl = "https://eu-central-1-1.aws.cloud2.influxdata.com"
	iforg = "CageTechnologies"
	ifbucket = "CAGEID01"
	iftoken = "1nwbGi_IcNmMZwJVytR6AzwnN48PHslUT1orUKFHZA0qd4G-ig27LZ8e7ef-8QcWilLrcu0t8ekwPfNgYoqF-A=="

	res = txrx.transceive(37,None,9,0,0)
	temp = round(int.from_bytes(res[2][3:5], signed=True) / 200.0,2)
	scale = int.from_bytes(res[2][6:8])

	print("Acquiring data (%.1f s)" %acq_time)
	tend = acq_time + time.time()
	
	while time.time() < tend  :

		res = txrx.transceive(37,None,3,0,0)
		if res[0] == 0 :
			dif = round(int.from_bytes(res[2][0:2], signed=True) / scale, 3)
	# disabled the following and moved to the start of ACQ for speed!
	#		temp = round(int.from_bytes(res[2][3:5], signed=True) / 200.0,2)
	#		scale = int.from_bytes(res[2][6:8])

			total0 += dif
			tcount0 += 1
			total1 += temp
			tcount1+= 1

			output = "venturi dif="
			output += "%.3f" % dif
			output += ",temp=%.2f" %temp
			output += ",scale=%.0f " %scale
			output += str(int(time.time() * 1000000))
			output += "\n"
			ptg.append(output) 

	av0 = total0 / tcount0
	av1 = total1 / tcount1
	acqrate = tcount0 / acq_time

	print("Raw: %.3f Pa, Temp: %.1f C, Scale: %.1f, Rate: %.1f Hz" %(av0,av1,scale,acqrate))
	print(tcount0, ", ", tcount1)

	res = input("Save data to influx? [Yn]")

	if res == "" or res=="Y" or res=="y" :
		print("Initialising InfluxDBClient")
		client = InfluxDBClient(url=ifurl, token=iftoken, org=iforg, enable_gzip=True, timeout=5_000)
		done = False
		while done == False :
			try :
				write_api = client.write_api(write_options=SYNCHRONOUS)
				print("Uploading....")
				write_api.write(bucket=ifbucket, org=iforg, record=ptg, write_precision=WritePrecision.US)
				done = True
			except :
				res = input("Upload failed! - retry? [Yn]")
				if res == "" or res=="Y" or res=="y" :
					print("Retrying upload")
				else :
					done = True
					print ("Upload cancelled!")
				
				
