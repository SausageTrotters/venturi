from struct import pack
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection, \
    I2cDevice, SensirionI2cCommand, CrcCalculator

import logging
logging.basicConfig(level=logging.DEBUG)

# Implement a command
class MyI2cCmdReadSerialNumber(SensirionI2cCommand):
    def __init__(self):
        super(MyI2cCmdReadSerialNumber, self).__init__(
            command=0x3624,
            tx_data=[],
            rx_length=9,
            read_delay=0.1,
            timeout=0,
            crc=CrcCalculator(8, 0x31, 0xFF),
        )

    def interpret_response(self, data):
        raw_response = SensirionI2cCommand.interpret_response(self, data)
        rawdata = int.from_bytes(raw_response[0:2], byteorder="big", signed=True)
        rawtemp = int.from_bytes(raw_response[3:5], byteorder="big", signed=True)
        rawscale = int.from_bytes(raw_response[6:8], byteorder="big", signed=True)
        return rawdata, rawtemp, rawscale

# Implement a device
class MyI2cDevice(I2cDevice):
    def __init__(self, connection, slave_address=0x25):
        super(MyI2cDevice, self).__init__(connection, slave_address)

    def read_serial_number(self):
        return self.execute(MyI2cCmdReadSerialNumber())


# Usage
with LinuxI2cTransceiver('/dev/i2c-1') as transceiver:
    device = MyI2cDevice(I2cConnection(transceiver))
    print("Serial Number: {}".format(device.read_serial_number()))


