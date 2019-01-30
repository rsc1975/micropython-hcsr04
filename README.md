# HC-SR04 Sensor driver in micropython

Micropython driver for the well-known untrasonic sensor [HC-SR04](https://www.mpja.com/download/hc-sr04_ultrasonic_module_user_guidejohn.pdf)

The driver has been tested on Wemos D1 mini PRO, but It should work on whatever other micropython board, 
if anyone find problems in other boards, please open an issue and we'll see.

## Motivation

The existing drivers in micropython are a bit old and they don't use the relatively new method `machine.time_pulse_us()` which
Is more accurate that whatever other method using pure python, besides the code is compliant with "standard" micropython,
there is no code for specific boards.

Finally I've added a method, `distance_mm()` that don't use floating point operations, for environments where there is no
floating point capabilities.

## Examples of use:

### How to get the distance

The `distance_cm()` method returns a `float` with the distance measured by the sensor.

```python
from hcsr04 import HCSR04

sensor = HCSR04(trigger_pin=16, echo_pin=0)

distance = sensor.distance_cm()

print('Distance:', distance, 'cm')
```

There is another method, `distance_mm()`, that returns the distance in milimeters (`int` type) and **no floating point is used**, designed 
for environments that doesn't support floating point operations.

```python
distance = sensor.distance_mm()

print('Distance:', distance, 'mm')
```
The default timeout is based on the sensor limit (4m), but we can also define a different timeout, 
passing the new value in microseconds to the constructor.

```python
from hcsr04 import HCSR04

sensor = HCSR04(trigger_pin=16, echo_pin=0, echo_timeout_us=1000000)

distance = sensor.distance_cm()

print('Distance:', distance, 'cm')
```

### Error management

When the driver reaches the timeout while is listening the echo pin the error is converted to `OSError('Out of range')`

```python
from hcsr04 import HCSR04

sensor = HCSR04(trigger_pin=16, echo_pin=0, echo_timeout_us=10000)

try:
    distance = sensor.distance_cm()
    print('Distance:', distance, 'cm')
except OSError as ex:
    print('ERROR getting distance:', ex)

```
