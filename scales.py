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
last_weight = -9999.99

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

exit = 0
offset0 = 0.0
offset1 = 0.0
done_first = False
last_time = 0

ifurl = "https://eu-central-1-1.aws.cloud2.influxdata.com"
iforg = "CageTechnologies"
ifbucket = "CAGEID01"
iftoken = "1nwbGi_IcNmMZwJVytR6AzwnN48PHslUT1orUKFHZA0qd4G-ig27LZ8e7ef-8QcWilLrcu0t8ekwPfNgYoqF-A=="
print("Initialising InfluxDBClient")
client = InfluxDBClient(url=ifurl, token=iftoken, org=iforg, enable_gzip=True, timeout=5_000)


while exit == False :

	if weight != -9999.99 :
		if(weight != last_weight) :
			print(weight)
			last_weight = weight
			output = "scales "
			output += "weight=%0.4f" %weight
			output += " " + str(int(time.time() * 1000))
			output += "\n"
			done = False
			while done == False :
				try :
					write_api = client.write_api(write_options=SYNCHRONOUS)
					print("Uploading....")
					write_api.write(bucket=ifbucket, org=iforg, record=output, write_precision=WritePrecision.MS)
					done = True
				except :
					pass

sexit=True
time.sleep(1)				
serport.close()				

