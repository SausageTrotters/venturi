from sensirion_i2c_driver import LinuxI2cTransceiver
import serial
import time
seq1 = {
	"seq01" : { "flow" : 0.1, "delay": 0.2, "command" : "1F,0.1,10,2"}
}


seq = {
	"seq01" : { "flow" : 0.1, "delay": 0.2, "command" : "1F,0.1,10,5"},
	"seq02" : { "flow" : 0.2, "delay": 0.2, "command" : "1F,0.2,5,5"},
	"seq03" : { "flow" : 0.3, "delay": 0.2, "command" : "1F,0.3,5,5"},
	"seq04" : { "flow" : 0.4, "delay": 0.2, "command" : "1F,0.4,5,5"},
	"seq05" : { "flow" : 0.5, "delay": 0.2, "command" : "1F,0.5,5,5"},
	"seq06" : { "flow" : 0.6, "delay": 0.2, "command" : "1F,0.6,5,5"},
	"seq07" : { "flow" : 0.7, "delay": 0.2, "command" : "1F,0.7,4,5"},
	"seq08" : { "flow" : 0.8, "delay": 0.2, "command" : "1F,0.8,4,5"},
	"seq09" : { "flow" : 0.9, "delay": 0.2, "command" : "1F,0.9,4,5"},
	"seq10" : { "flow" : 1.0, "delay": 0.1, "command" : "1F,1.0,2,5"},
	"seq11" : { "flow" : 1.1, "delay": 0.1, "command" : "1F,1.1,2,5"},
	"seq12" : { "flow" : 1.2, "delay": 0.1, "command" : "1F,1.2,2,5"},
	"seq13" : { "flow" : 1.3, "delay": 0.1, "command" : "1F,1.3,2,5"},
	"seq14" : { "flow" : 1.4, "delay": 0.1, "command" : "1F,1.4,2,5"},
	"seq15" : { "flow" : 1.5, "delay": 0.1, "command" : "1F,1.5,2,5"},
	"seq16" : { "flow" : 1.6, "delay": 0.1, "command" : "1F,1.6,2,5"},
	"seq17" : { "flow" : 1.7, "delay": 0.1, "command" : "1F,1.7,2,5"},
	"seq18" : { "flow" : 1.8, "delay": 0.1, "command" : "1F,1.8,2,5"},
	"seq19" : { "flow" : 1.9, "delay": 0.1, "command" : "1F,1.9,2,5"}
}


def command(data):
	serport.write(bytes(data + "\r", 'utf-8'))
	time.sleep(0.05)
	rc = serport.in_waiting
	if rc > 0 :
		return int(serport.read(rc))
	else :
		return None


serport = serial.Serial(port='/dev/ttyUSB0', baudrate=115200)
print("waiting for serial!", end = " - ", flush = True)
time.sleep(2.0)
#serport.write(bytes("1hg\r", 'utf-8'))
print("Homing", end = " - ", flush = True)
command("1hg")

while command("1hs") != 5 :
	pass
print("Complete")

txrx = LinuxI2cTransceiver('/dev/i2c-1')
txrx.transceive(37,b'\x36\x03',None,0,0)
 
time.sleep(2.0)
res = txrx.transceive(37,None,9,0,0)
scale = round(int.from_bytes(res[2][6:8], signed=True) , 2)
if scale == 0.0 :
	print("Scalefactor = 0!")
	exit()
zero = round(int.from_bytes(res[2][0:2], signed=True) / scale, 2)

res = input("Enter output filename: ")
f = open("data/"+res+".csv", "x")
f.write("flow,suck,blow,temp\n")


print("Scale: ", scale, " Zero: ", zero)

#
for key in seq :

	suck_av_dif = 0.0
	suck_av_temp = 0.0
	suck_av_count = 0
	blow_av_dif = 0.0
	blow_av_temp = 0.0
	blow_av_count = 0

	pdelay_done = False
	ndelay_done = False

	command(seq[key]["command"])
	while True :
		vel = command("1mv")
		if vel == 0 :
			vel = command("1mv")
			if vel == 0 :
				break
		if vel == 31 :
			if pdelay_done == False : 
				time.sleep(seq[key]["delay"])
				pdelay_done = True
			ndelay_done = False
			res = txrx.transceive(37,None,9,0,0)
			dif = round(int.from_bytes(res[2][0:2], signed=True) / scale, 2)
			temp = round(int.from_bytes(res[2][3:5], signed=True) / 200.0,2)
			suck_av_dif += dif
			suck_av_temp += temp
			suck_av_count += 1
		#	print("stable suck!, dif: ", dif, " temp: ", temp)
		if vel == -31 :
			if ndelay_done == False :
				time.sleep(seq[key]["delay"])
				ndelay_done = True
			pdelay_done = False
			res = txrx.transceive(37,None,9,0,0)
			dif = round(int.from_bytes(res[2][0:2], signed=True) / scale, 2)
			temp = round(int.from_bytes(res[2][3:5], signed=True) / 200.0,2)
			blow_av_dif += dif
			blow_av_temp += temp
			blow_av_count += 1
		#	print("stable blow!, dif: ", dif, " temp: ", temp)

	suck_av = round(suck_av_dif / suck_av_count - zero,2)
	blow_av = round(blow_av_dif / blow_av_count- zero ,2)
	temp_av = round(blow_av_temp / blow_av_count,2)

	print("Flow: ", seq[key]["flow"]," Suck: ", suck_av, " Blow: ", blow_av, "Temp: ", temp_av) 
	str = "{:.2f}".format(seq[key]["flow"])
	str += "," + "{:.2f}".format(suck_av)
	str += "," + "{:.2f}".format(blow_av)
	str += "," + "{:.2f}".format(temp_av)
	str += "\n"
	f.write(str)

#print("Suck average dif: ", round(suck_av_dif / suck_av_count,2), " suck average temp: ", round(suck_av_temp / suck_av_count, 2))
#print("Blow average dif: ", round(blow_av_dif / blow_av_count,2), " blow average temp: ", round(blow_av_temp / blow_av_count, 2))

#for x in range(1000) :
#  res = txrx.transceive(37,None,9,0,0)
#  dif = round(int.from_bytes(res[2][0:2], signed=True) / 60.0, 2)
#  temp = round(int.from_bytes(res[2][3:5], signed=True) / 200.0,2)
#  print("dif: ", dif, "temp: ", temp)


