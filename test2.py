import smbus
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

bus0=smbus.SMBus(0)
bus1=smbus.SMBus(1)
address = 0x6c
last0 = 0
last1 = 0
tend = 10.0 + time.time()
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

exit = 0

while exit == False :
	res = input("Acquire data (10s)? [Yn]")
	if res != "" and res!="Y" and res!="y" :
		break

	print("Acquiring data (10s)")
	
	while time.time() < tend  :
	
		res0 = bus0.read_word_data(address, 0x30)
		if res0 > 32767 :
			res0 = res0 - 65536
		res0 = -4000 + (res0 + 26214) / 52428 * 8000.0
		total0 = total0 + res0
		tcount0 = tcount0 + 1
	
		res1 = bus1.read_word_data(address, 0x30)
		if res1 > 32767 :
			res1 = res1 - 65536
		res1 = -125 + (res1 + 26214) / 52428 * 250.0
		total1 = total1 + res1
		tcount1 = tcount1 + 1 
	
		output = "venturi static="
		output += "%.1f" % res0
		output += ",dif=%.3f " %res1
		output += str(int(time.time() * 1000))
		output += "\n"
		ptg.append(output) 
	
	av0 = total0 / tcount0
	av1 = total1 / tcount1
	
	print("%.1f" %av0," ","%.3f" %av1)
	
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
				
				
