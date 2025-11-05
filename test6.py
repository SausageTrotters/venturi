from sensirion_i2c_driver import LinuxI2cTransceiver

txrx = LinuxI2cTransceiver('/dev/i2c-1')
txrx.transceive(37,b'\x36\x03',None,0,0)

for x in range(1000) :
  res = txrx.transceive(37,None,9,0,0)
  dif = round(int.from_bytes(res[2][0:2], signed=True) / 60.0, 2)
  temp = round(int.from_bytes(res[2][3:5], signed=True) / 200.0,2)
  print("dif: ", dif, "temp: ", temp)



