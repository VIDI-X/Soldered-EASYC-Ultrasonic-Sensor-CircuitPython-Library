# FILE: UltrasonicSensor.py
# AUTHOR: VIDI X Team — adapted for CircuitPython (I2C mode) from the MicroPython original by Josip Šimun Kuči @ Soldered
# LICENSE: MIT
#
# BRIEF: CircuitPython I2C driver for an HC-SR04–style ultrasonic module with an onboard MCU
#        exposing the following registers:
#          0x00: command (send the register address only to trigger a measurement)
#          0x01: distance (little‑endian, centimeters)
#          0x02: echo duration (little‑endian, microseconds)
#
"""
Usage
-----

# Basic I2C setup and quick check:
    import time, board
    from UltrasonicSensor import UltrasonicSensor
    
    i2c = board.I2C() # or: busio.I2C(board.GPIO32, board.GPIO33) on VIDI X
    us = UltrasonicSensor(i2c, address=0x34)
    
    us.takeMeasure()
    time.sleep(0.12) # give the sensor ~120 ms
    print(us.getDistance(), "cm", us.getDuration(), "us")

# Stable, blocking reading that returns the first non-zero measurement:
    d_cm = us.read_cm_blocking(settle_s=0.12) # timeout is 0.30 s by default
    print("Blocking:", d_cm, "cm")

# Averaging for smoother output:
    d_avg = us.distance_cm_avg(n=5, settle_s=0.08)
    print("Average:", d_avg, "cm")

# Air temperature compensation (speed of sound ~ 331.3 + 0.606 * T[°C]):
    # If you already have an IMU, use its thermometer.
    from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
    imu = LSM6DSOX(i2c, address=0x6B) # change the address if yours is 0x6A
    temp_c = imu.temperature
    
    d_comp = us.distance_cm_comp(temp_c, base_temp_c=20.0, settle_s=0.12)
    print("Temp-comp:", f"{d_comp:.2f} cm @ {temp_c:.1f}°C")

Note:
The first reading after power-up or configuration change may be 0 — feel free to
ignore it. If you are working very close (a few cm), increase settle_s to 0.15–0.20 s.
"""
#
# License: MIT

import time
from adafruit_bus_device.i2c_device import I2CDevice

# Register map (as per MicroPython version)
TAKE_MEAS_REG = 0x00   # write: send address only to trigger
DISTANCE_REG  = 0x01   # read: 2 bytes, little-endian, centimeters
DURATION_REG  = 0x02   # read: 2 bytes, little-endian, microseconds

class UltrasonicSensor:
    def __init__(self, i2c, address=0x34):
        # Accept either board.I2C() or busio.I2C(...)
        self._device = I2CDevice(i2c, address)
        self.address = address

    # --- low-level helpers -------------------------------------------------
    def _write_cmd_single(self, value):
        # Single-byte write (no data payload). Matches MicroPython send_address().
        with self._device as i2c:
            i2c.write(bytes([value]))

    def _read_into(self, reg, buf):
        # Standard write-then-readinto with repeated START (no STOP in-between).
        # This mirrors typical readfrom_mem semantics used in MicroPython drivers.
        with self._device as i2c:
            i2c.write_then_readinto(bytes([reg]), buf)

    def _read_u16le(self, reg):
        b = bytearray(2)
        self._read_into(reg, b)
        return b[0] | (b[1] << 8)

    # --- public API --------------------------------------------------------
    def takeMeasure(self):
        # Trigger a measurement by sending ONLY the register address as a command.
        self._write_cmd_single(TAKE_MEAS_REG)

    def getDistance(self):
        # Returns centimeters as float (compatible with the user's expectations)
        return float(self._read_u16le(DISTANCE_REG))

    def getDuration(self):
        # Returns echo pulse width in microseconds as int
        return int(self._read_u16le(DURATION_REG))

    # --- convenience helpers ----------------------------------------------
    def read_cm_blocking(self, timeout_s=0.30, settle_s=0.12):
        """Okidaj i čekaj do prve nenulte mjere ili do isteka vremena."""
        end = time.monotonic() + float(timeout_s)
        while True:
            self.takeMeasure()
            time.sleep(settle_s)
            d = self.getDistance()
            if d > 0.0 or time.monotonic() >= end:
                return float(d)

    def distance_cm_avg(self, n=5, settle_s=0.08):
        """Vrati prosjek od n nenultih mjerenja."""
        total = 0.0
        count = 0
        for _ in range(int(n)):
            self.takeMeasure()
            time.sleep(settle_s)
            d = self.getDistance()
            if d > 0.0:
                total += d
                count += 1
        return (total / count) if count else 0.0

    def distance_cm_comp(self, temp_c, base_temp_c=20.0, settle_s=0.12):
        """Temperaturna kompenzacija na osnovu brzine zvuka ~ 331.3 + 0.606 * T[°C]."""
        v  = 331.3 + 0.606 * float(temp_c)
        v0 = 331.3 + 0.606 * float(base_temp_c)
        d  = self.read_cm_blocking(settle_s=settle_s)
        return d * (v / v0)
