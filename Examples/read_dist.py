import time
import board
from UltrasonicSensor import UltrasonicSensor

# Prefer board.I2C() since your scan shows the device there; busio.I2C(GPIO32,GPIO33) also works.
i2c = board.I2C()

sensor = UltrasonicSensor(i2c, address=0x34)

while True:
    sensor.takeMeasure()
    time.sleep(0.12)                 # give the module time to acquire
    dist_cm = sensor.getDistance()
    dur_us  = sensor.getDuration()
    print(f"Distance: {dist_cm:.1f} cm  |  Echo: {dur_us} us")
    time.sleep(0.2)
