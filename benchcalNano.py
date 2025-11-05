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
	"seq17" : { "flow" : 1.7, "delay": 0.1, "command" : "1F,1.7,2,5"}
}


def command(port, data):
	port.write(bytes(data + "\r", 'utf-8'))
	time.sleep(0.05)
	rc = port.in_waiting
	if rc > 0 :
		return int(port.read(rc))
	else :
		return None

def commandall(port, data):
	port.write(bytes(data + "\r", 'utf-8'))
	time.sleep(0.1)
	rc = port.in_waiting
	if rc > 0 :
		return port.read(rc)
	else :
		return None


serport = serial.Serial(port='/dev/ttyUSB1', baudrate=115200)
sermf = serial.Serial(port='/dev/ttyUSB0', baudrate=115200)

print("waiting for serial!", end = " - ", flush = True)
time.sleep(2.0)
#serport.write(bytes("1hg\r", 'utf-8'))
print("Homing", end = " - ", flush = True)
command(serport, "1hg")

while command(serport, "1hs") != 5 :
	pass
print("Complete")

res = input("Enter output filename: ")
f = open("data/"+res+".csv", "x")
f.write("flow,suck,blow,temp\n")

print(commandall(sermf,"canbus10"))
time.sleep(1.0)
ret = commandall(sermf,"aveng").decode('utf-8').split()
zero = float(ret[1])

print(" Zero: ", zero)

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

	command(serport, seq[key]["command"])
	while True :
		vel = command(serport, "1mv")
		if vel == 0 :
			vel = command(serport, "1mv")
			if vel == 0 :
				break
		if vel == 31 :
			if pdelay_done == False : 
				time.sleep(seq[key]["delay"])
				pdelay_done = True
			ndelay_done = False

#			spos = command(serport,"1mp")
#			time.sleep(0.2)
#			dpos = command(serport,"1mp") - spos
#			print("Dpos: ", dpos)

			ret = commandall(sermf,"aveng").decode('utf-8').split()
			dif = float(ret[1])
			temp = float(ret[3])
			suck_av_dif += dif
			suck_av_temp += temp
			suck_av_count += 1
		if vel == -31 :
			if ndelay_done == False :
				time.sleep(seq[key]["delay"])
				ndelay_done = True
			pdelay_done = False
			ret = commandall(sermf,"aveng").decode('utf-8').split()
			dif = float(ret[1])
			temp = float(ret[3])
			blow_av_dif += dif
			blow_av_temp += temp
			blow_av_count += 1

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

