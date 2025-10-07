# Soldered-EASYC-Ultrasonic-Sensor-CircuitPython-Library
CircuitPython Library for Ultrasonic Sensor with I2C (EASYC,VIDIIC,qwiic) from Soldered

# TL;RD

README.md explains what the driver does, how to copy it to a VIDI X board running CircuitPython, how to run both example scripts, and how the temperature offset & micro-switch behavior work.
##
---

# VIDI X Ultrasonic Sensor (CircuitPython)

This library lets a VIDI X (ESP32) read distance from an I²C ultrasonic module at address `0x34`, and optionally adjust that distance using the board’s built-in temperature sensor on `GPIO26`. The core driver is `UltrasonicSensor.py`, and there are two example programs: one for basic distance and echo time, and one that uses the temperature sensor to improve accuracy.   

## What’s inside

The driver talks to a small microcontroller inside the ultrasonic module. It sends a “trigger” command, then reads two 16-bit values: distance in centimeters and echo pulse width in microseconds. Both values are little-endian and live at registers `0x01` and `0x02`. Trigger is issued by writing just the register address `0x00` with no payload. Those details are already baked into the driver, you don’t have to manage registers yourself. 

* `UltrasonicSensor.py` — the CircuitPython driver with a simple, student-friendly API. It exposes `takeMeasure()`, `getDistance()`, `getDuration()`, plus a blocking read and averaging helpers. 
* `read_dist.py` — the smallest possible demo: measure distance and echo over and over. 
* `read_dist_temp.py` — a practical demo for science lessons: read the onboard temperature sensor on `GPIO26`, apply a default −2 °C correction, warn if the micro-switch is not in `TEMP` position, and show compensated distance. 

## Getting ready

Make sure your VIDI X is running CircuitPython and that the `adafruit_bus_device` library is present in `lib/` on the CIRCUITPY drive, because the driver uses `I2CDevice` under the hood. Then copy the files from this repo to the root of the CIRCUITPY drive so they sit next to each other.

Wiring on VIDI X is already done on the board headers. The I²C ultrasonic module appears at `0x34` on the default `board.I2C()` bus, so you don’t need to set pins manually. If you ever need to, the alternate explicit bus is `busio.I2C(board.GPIO32, board.GPIO33)`. The onboard temperature sensor is read as an analog input on `GPIO26`.   

## Quick start: read distance

Save the following as `code.py`, or open the REPL and paste it. It matches the included `read_dist.py`.

```python
import time
import board
from UltrasonicSensor import UltrasonicSensor

i2c = board.I2C()                 # VIDI X default I2C bus
sensor = UltrasonicSensor(i2c, address=0x34)

while True:
    sensor.takeMeasure()
    time.sleep(0.12)              # give the module time to measure
    dist_cm = sensor.getDistance()
    dur_us  = sensor.getDuration()
    print(f"Distance: {dist_cm:.1f} cm  |  Echo: {dur_us} us")
    time.sleep(0.2)
```

That script repeatedly prints the distance (in centimeters) and the echo pulse duration (in microseconds). The `0.12 s` wait matches the timing used in the example file. 

## Science mode: temperature-aware distance

Air temperature slightly changes the speed of sound. The `read_dist_temp.py` demo shows how to read the VIDI X onboard temperature sensor on `GPIO26`, apply a small calibration offset, and compensate distance accordingly. It also warns if the reading is above 60 °C, which often means the micro-switch is not set to `TEMP`. 

```python
import time, board, analogio
from UltrasonicSensor import UltrasonicSensor

I2C_ADDRESS       = 0x34
TEMP_PIN          = board.GPIO26
TEMP_OFFSET_C     = -2.0   # default correction for your board
BASE_TEMP_C       = 20.0
SETTLE_S          = 0.12
AVG_SAMPLES       = 5
OVERHEAT_WARNING  = 60.0

i2c = board.I2C()
us = UltrasonicSensor(i2c, address=I2C_ADDRESS)
temp_adc = analogio.AnalogIn(TEMP_PIN)

def read_temperature_c(adc):
    raw = adc.value
    mv = raw * (adc.reference_voltage * 1000.0 / 65535.0)
    return (mv - 500.0) / 10.0

print("Starting measurements… Press Ctrl+C to stop.")
while True:
    temp_c = read_temperature_c(temp_adc) + TEMP_OFFSET_C
    if temp_c > OVERHEAT_WARNING:
        print("Warning: Temperature is high — check the micro-switch (TEMP position).")
    raw_cm = us.read_cm_blocking(settle_s=SETTLE_S)
    avg_cm = us.distance_cm_avg(n=AVG_SAMPLES, settle_s=0.08)
    comp_cm = us.distance_cm_comp(temp_c, base_temp_c=BASE_TEMP_C, settle_s=SETTLE_S)
    print(f"Temp: {temp_c:4.1f} °C | Raw: {raw_cm:6.2f} cm | Avg: {avg_cm:6.2f} cm | Comp: {comp_cm:6.2f} cm")
    time.sleep(0.30)
```

The temperature conversion formula is the same one shown in the standalone `temp.py` helper: convert ADC to millivolts using the reference voltage, then compute `°C = (mV − 500) / 10`. The `−2 °C` default offset simply nudges the reading toward your board’s real-world behavior.  

## The driver API at a glance

You don’t have to remember registers. Use these methods from `UltrasonicSensor`:

* `takeMeasure()` starts a new measurement cycle on the sensor.
* `getDistance()` returns the distance in centimeters as a float.
* `getDuration()` returns the echo pulse width in microseconds as an integer.
* `read_cm_blocking(settle_s=0.12, timeout_s=0.30)` triggers and waits for the first non-zero reading, useful to avoid “0 cm” right after power-up.
* `distance_cm_avg(n=5, settle_s=0.08)` averages several valid readings to stabilize the value.
* `distance_cm_comp(temp_c, base_temp_c=20.0, settle_s=0.12)` measures and returns a temperature-compensated distance using the classic speed-of-sound model. 

## Classroom ideas

Use the basic script to measure different objects and chart how distance changes while a student moves their hand. Switch to the temperature demo and ask students to gently warm the sensor’s environment and watch the compensated distance stay steadier than the uncompensated one. For math integration, have them compute averages manually and compare with what the `distance_cm_avg` helper prints. All of this works without needing to explain I²C frames or bit-endian order.

## Troubleshooting

If you see `0 cm` right after turning everything on, that’s normal for the first cycle; the blocking helper or a short delay handles it. If you get an input/output error from I²C, increase `settle_s` to `0.15–0.20` seconds to give the sensor time to finish a cycle before you read again. If the temperature prints above 60 °C, check that the micro-switch is in the `TEMP` position, otherwise the analog input isn’t connected as expected. The example files already use safe timings and messages tailored for VIDI X.  

## Credits and license

The driver is **VIDI X Team — adapted for CircuitPython (I²C mode) from the MicroPython original by Josip Šimun Kuči @ Soldered.** License is MIT; see headers in the Python files. 
