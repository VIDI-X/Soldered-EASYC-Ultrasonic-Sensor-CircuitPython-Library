# read_dist_temp.py — VIDI X (ESP32) + UltrasonicSensor + on-board temp (GPIO26)
# Author: VIDI X Team
# License: MIT
#
# Description:
#   Reads the on-board temperature sensor via analog input on GPIO26,
#   applies a default offset of -2°C (calibration), and uses the corrected
#   temperature to compensate ultrasonic distance. If temperature exceeds
#   60°C, it warns that the micro-switch is probably not in the TEMP position.
#
# Requirements:
#   - UltrasonicSensor.py in the same directory (I2C address 0x34 by default)
#   - CircuitPython with adafruit_bus_device installed
#
import time
import board
import analogio

from UltrasonicSensor import UltrasonicSensor

# ---------- Configuration ----------
I2C_ADDRESS       = 0x34        # your ultrasonic module address
TEMP_PIN          = board.GPIO26
TEMP_OFFSET_C     = -2.0        # default calibration offset (°C)
BASE_TEMP_C       = 20.0        # baseline for compensation
SETTLE_S          = 0.12        # settle time after triggering a measurement
AVG_SAMPLES       = 5           # averaging count for smoother output
OVERHEAT_WARNING  = 60.0        # warn if measured temp is above this

# ---------- Helpers ----------
def read_temperature_c(adc: analogio.AnalogIn) -> float:
    """Read temperature sensor on GPIO26 and return Celsius.
    Formula: tempC = (mV - 500) / 10, where mV = raw * (Vref*1000/65535).
    """
    raw = adc.value
    mv = raw * (adc.reference_voltage * 1000.0 / 65535.0)
    temp_c = (mv - 500.0) / 10.0
    return float(temp_c)

# ---------- Setup ----------
# I2C bus (board.I2C() works on VIDI X; alternatively: busio.I2C(board.GPIO32, board.GPIO33))
i2c = board.I2C()

# Ultrasonic sensor
us = UltrasonicSensor(i2c, address=I2C_ADDRESS)

# On-board temperature sensor
temp_adc = analogio.AnalogIn(TEMP_PIN)

print("Reference voltage (V):", temp_adc.reference_voltage)
print("Starting measurements… Press Ctrl+C to stop.\n")

# ---------- Loop ----------
while True:
    # Read and calibrate temperature
    temp_c = read_temperature_c(temp_adc) + TEMP_OFFSET_C

    # Warn if switch is likely not in TEMP position
    if temp_c > OVERHEAT_WARNING:
        print("Warning: Temperature reads {:.1f}°C — check the micro-switch (should be in TEMP).".format(temp_c))

    # Get distance readings
    raw_cm = us.read_cm_blocking(settle_s=SETTLE_S)
    avg_cm = us.distance_cm_avg(n=AVG_SAMPLES, settle_s=0.08)
    comp_cm = us.distance_cm_comp(temp_c, base_temp_c=BASE_TEMP_C, settle_s=SETTLE_S)

    # Pretty print one line
    print("Temp: {:5.1f}°C (offset {:+.1f}) | Raw: {:6.2f} cm | Avg: {:6.2f} cm | Comp: {:6.2f} cm"
          .format(temp_c, TEMP_OFFSET_C, raw_cm, avg_cm, comp_cm))

    time.sleep(0.30)
