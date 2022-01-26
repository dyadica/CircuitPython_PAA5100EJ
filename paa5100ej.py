import busio
import board
import digitalio
import time
import struct

from adafruit_bus_device.spi_device import SPIDevice

class PAA5100EJ():
    def __init__(self, spi, cs):        
        
        print("Initializing the PAA5100EJ")
        
        """define the SPI"""
        self.spi_device = SPIDevice(spi, cs)
        
        """Power up and reset"""
        self._write_to_reg(0x3a, 0x5a)            
        time.sleep(0.5)
        
        """
        Test the SPI communication against
        chipId and inverse chipId
        """
        
        chipId = self._read(0x00)
        dIpihc = self._read(0x5F)
        
        print("Chip +ID:", chipId, " Chip -ID:", dIpihc)
        
        """Use the Chip ID's to test SPI comms"""        
        if chipId!= 0x49 and dIpihc != 0xB8:
            print("Failed comms test!")
            return
        
        print("Passed comms test!")        
        print("Reading registers")
        
        """Read the data registers"""
        
        self._read(0x02)
        self._read(0x03)
        self._read(0x04)
        self._read(0x05)
        self._read(0x06)    
    
        """Initialize the device registers. You dont seem to need
        the secret ones for the PAA5100EJ!"""
        
        self._init_registers_secret()
        self._init_registers()
        self._init_registers_led()
        
        """Get the product id and revision"""
        product_id, revision = self.get_id()        
        print(product_id, revision)
        
        if product_id != 0x49 or revision != 0x00:
            raise RuntimeError("Invalid Product ID or Revision for PAA5100EJ/PAA5100EJ: 0x{:02x}/0x{:02x}".format(product_id, revision))

    def get_id(self):
        """Get chip ID and revision from PMW3901/PAA5100EJ."""
        return self._read(0x00, 2)
    
    """function for writing to a specific register"""
    def _write_to_reg(self, reg, val):
        with self.spi_device as spi:
            spi.write(bytearray([reg | 0x80, val]))
    
    """function for bulk writing of group data (reg,val)
    to specific registers"""
    def _bulk_write(self, data):
        for x in range(0, len(data), 2):
            reg, val = data[x:x + 2]
            if reg == "WAIT":
                #print("Sleeping for: {:02d}ms".format(val))
                time.sleep(val / 1000)
            else:
                #print("Writing: {:02x} to {:02x}".format(reg, val))
                self._write_to_reg(reg, val)    
    
    """function to read data in to a buffer of given
    length via calling specific register"""
    def _read(self, register, length=1):
        result = []
        with self.spi_device as spi:
            for x in range(length):
                val = bytearray(2)
                cmd = bytearray(2)
                cmd[0] = register+x
                cmd[1] = 0
                spi.write_readinto(cmd, val)
                result.append(val[1])

            if length == 1:
                return result[0]
            else:
                return result
    
    """function to read data in to a buffer of given
    length via calling specific register"""
    def _register_read(self, register, length=1):
        with self.spi_device as spi:
            spi.write(bytearray([register]))
            result = bytearray(length)
            spi.readinto(result)
            return result
    
    """function used to start and stop the leds"""
    def set_led_state(self, state=False):
        if state == True:
            self._bulk_write([
            "WAIT", 0xF0,
            0x7f, 0x14,
            0x6f, 0x1c,
            0x7f, 0x00
            ])
        else:
            self._bulk_write([
            "WAIT", 0xF0,
            0x7f, 0x14,
            0x6f, 0x00,
            0x7f, 0x00
            ])    
    
    """Set orientation of PMW3901 in increments of 90 degrees.
    :param degrees: rotation in multiple of 90 degrees"""        
    def set_rotation(self, degrees=0):
        
        if degrees == 0:
            self.set_orientation(invert_x=True, invert_y=True, swap_xy=True)
        elif degrees == 90:
            self.set_orientation(invert_x=False, invert_y=True, swap_xy=False)
        elif degrees == 180:
            self.set_orientation(invert_x=False, invert_y=False, swap_xy=True)
        elif degrees == 270:
            self.set_orientation(invert_x=True, invert_y=False, swap_xy=False)
        else:
            raise TypeError("Degrees must be one of 0, 90, 180 or 270")

    """Set orientation of PMW3901 manually.Swapping is performed before flipping.
    :param invert_x: invert the X axis
    :param invert_y: invert the Y axis
    :param swap_xy: swap the X/Y axes"""
    def set_orientation(self, invert_x=True, invert_y=True, swap_xy=True):                
        value = 0
        if swap_xy:
            value |= 0b10000000
        if invert_y:
            value |= 0b01000000
        if invert_x:
            value |= 0b00100000
            
        self._write_to_reg(0x5b, value)        
    
    """Get motion data from PMW3901 using burst read. Reads 12 bytes
    sequentially from the PMW3901 and validates motion data against
    the SQUAL and Shutter_Upper values. Returns Delta X and Delta Y
    indicating 2d flow direction and magnitude.
    :param timeout: Timeout in seconds"""
    def get_motion(self, timeout=5):
        
        t_start = time.time()
        
        while time.time() - t_start < timeout:
            
            with self.spi_device as spi:
                cmd = bytearray([0x16] + [0 for x in range(12)])
                #print(cmd)
                val = bytearray(13)
                spi.write_readinto(cmd, val)
                #print(val)

            (_, dr, obs, x, y, quality, raw_sum, raw_max, raw_min,
             shutter_upper, shutter_lower) = struct.unpack("<BBBhhBBBBBB", val)

            if dr & 0b10000000 and not (quality < 0x19 and shutter_upper == 0x1f):
                return x, y

            time.sleep(0.01)

        raise RuntimeError("Timed out waiting for motion data.")
    
    """Get motion data from PMW3901. Returns Delta X and Delta Y
    indicating 2d flow direction and magnitude.
    :param timeout: Timeout in seconds"""
    def get_motion_slow(self, timeout=5):
        
        t_start = time.time()
        
        while time.time() - t_start < timeout:
            data = self._read(0x02, 5)
            dr, x, y = struct.unpack("<Bhh", bytearray(data))
            if dr & 0b10000000:
                return x, y
            time.sleep(0.001)

        raise RuntimeError("Timed out waiting for motion data.")
    
    def _init_registers(self):
        
        print("Init Registers")
        
        self._bulk_write([
            0x7f, 0x00,
            0x61, 0xad,
            0x7f, 0x03,
            0x40, 0x00,
            0x7f, 0x05,

            0x41, 0xb3,
            0x43, 0xf1,
            0x45, 0x14,
            0x5b, 0x32,
            0x5f, 0x34,
            0x7b, 0x08,
            0x7f, 0x06,
            0x44, 0x1b,
            0x40, 0xbf,
            0x4e, 0x3f,
            0x7f, 0x08,
            0x65, 0x20,
            0x6a, 0x18,

            0x7f, 0x09,
            0x4f, 0xaf,
            0x5f, 0x40,
            0x48, 0x80,
            0x49, 0x80,

            0x57, 0x77,
            0x60, 0x78,
            0x61, 0x78,
            0x62, 0x08,
            0x63, 0x50,
            0x7f, 0x0a,
            0x45, 0x60,
            0x7f, 0x00,
            0x4d, 0x11,

            0x55, 0x80,
            0x74, 0x21,
            0x75, 0x1f,
            0x4a, 0x78,
            0x4b, 0x78,

            0x44, 0x08,
            0x45, 0x50,
            0x64, 0xff,
            0x65, 0x1f,
            0x7f, 0x14,
            0x65, 0x67,
            0x66, 0x08,
            0x63, 0x70,
            0x7f, 0x15,
            0x48, 0x48,
            0x7f, 0x07,
            0x41, 0x0d,
            0x43, 0x14,

            0x4b, 0x0e,
            0x45, 0x0f,
            0x44, 0x42,
            0x4c, 0x80,
            0x7f, 0x10,

            0x5b, 0x02,
            0x7f, 0x07,
            0x40, 0x41,
            0x70, 0x00,
            "WAIT", 0x0A,  # Sleep for 10ms

            0x32, 0x44,
            0x7f, 0x07,
            0x40, 0x40,
            0x7f, 0x06,
            0x62, 0xf0,
            0x63, 0x00,
            0x7f, 0x0d,
            0x48, 0xc0,
            0x6f, 0xd5,
            0x7f, 0x00,

            0x5b, 0xa0,
            0x4e, 0xa8,
            0x5a, 0x50,
            0x40, 0x80,
        ])
        
    def _init_registers_secret(self):
        
        print("Init Registers Secret")
        
        self._bulk_write([
            0x7f, 0x00,
            0x55, 0x01,
            0x50, 0x07,

            0x7f, 0x0e,
            0x43, 0x10
        ])
        
        if self._read(0x67) & 0b10000000:
            self._write_to_reg(0x48, 0x04)
        else:
            self._write_to_reg(0x48, 0x02)
            
        self._bulk_write([
            0x7f, 0x00,
            0x51, 0x7b,

            0x50, 0x00,
            0x55, 0x00,
            0x7f, 0x0E
        ])
        
        if self._read(0x73) == 0x00:
            c1 = self._read(0x70)
            c2 = self._read(0x71)
            if c1 <= 28:
                c1 += 14
            if c1 > 28:
                c1 += 11
            c1 = max(0, min(0x3F, c1))
            c2 = (c2 * 45) // 100
            self._bulk_write([
                0x7f, 0x00,
                0x61, 0xad,
                0x51, 0x70,
                0x7f, 0x0e
            ])
            
            self._write_to_reg(0x70, c1)
            self._write_to_reg(0x71, c2)
        
    def _init_registers_led(self):
        
        print("Init Registers Led")
        
        # Switch on LED dosent seem to work here?
        self._bulk_write([
            "WAIT", 0xF0,
            0x7f, 0x14,
            0x6f, 0x1c,
            0x7f, 0x00
        ])
         
         