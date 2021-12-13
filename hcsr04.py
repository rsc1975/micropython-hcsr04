from machine import Pin, time_pulse_us
from utime import sleep_us
from math import sqrt

__version__ = '0.3.0'
__author__ = 'Roberto Sánchez'
__license__ = "Apache License 2.0. https://www.apache.org/licenses/LICENSE-2.0"

DEFAULT_TEMPERATURE=20

class HCSR04:
    """
    Driver to use the untrasonic sensor HC-SR04.
    The sensor range is between 2cm and 4m.

    The timeouts received listening to echo pin are converted to OSError('Out of range')

    """
    # echo_timeout_us is based in chip range limit (400cm)
    # air_temp is the temperature of the air. It is setted by default to 20°C
    # air_temp must be defined in order to calculate the speed of sound in the air. It must be passed in Celsius
    def __init__(self, trigger_pin, echo_pin, echo_timeout_us=500*2*30, air_temp=DEFAULT_TEMPERATURE):
        """
        trigger_pin: Output pin to send pulses
        echo_pin: Readonly pin to measure the distance. The pin should be protected with 1k resistor
        echo_timeout_us: Timeout in microseconds to listen to echo pin. 
        By default is based in sensor limit range (4m)
        """
        # the working temperature of the sensor is between -15°C and 70°C according to the datasheet
        self.max_working_temp = 70
        self.min_working_temp = -15

        # speed of sound in the air depends by the temperature of air
        # so first is checked if the air temp is in the working range of the sensor, then will be calculated the speed of sound
        # speed of sound is needed to calculate the distance from the sensor to the object (formula is distance = speed of sound/time)
        self.air_temperature = self._check_air_temp(air_temp)
        self.sound_speed = self._get_sound_speed()
        
        self.echo_timeout_us = echo_timeout_us
        # Init trigger pin (out)
        self.trigger = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        self.trigger.value(0)

        # Init echo pin (in)
        self.echo = Pin(echo_pin, mode=Pin.IN, pull=None)
        
    
    def _check_air_temp(self, temperature):
        """
        Check if air temp is in the working range of the sensor
        """
        if self.min_working_temp <= temperature <= self.max_working_temp:
            return temperature
        else:
            #Temperature is out of working range
            return DEFAULT_TEMPERATURE

    def _get_sound_speed(self):
        """
        Calculate speed of sound in the air (which depends by air temperature)
        and divide for 1000 in order to convert the speed from m/s to mm/microseconds
        """
        ss = 20.05*(sqrt(self.air_temperature+273.15))
        ss = ss / 1000 # conversion from meters / seconds in millimeters / microseconds
        return ss

    def _send_pulse_and_wait(self):
        """
        Send the pulse to trigger and listen on echo pin.
        We use the method `machine.time_pulse_us()` to get the microseconds until the echo is received.
        """
        self.trigger.value(0) # Stabilize the sensor
        sleep_us(5)
        self.trigger.value(1)
        # Send a 10us pulse.
        sleep_us(10)
        self.trigger.value(0)
        try:
            pulse_time = time_pulse_us(self.echo, 1, self.echo_timeout_us)
            # time_pulse_us returns -2 if there was timeout waiting for condition; and -1 if there was timeout during the main measurement. It DOES NOT raise an exception
            # ...as of MicroPython 1.17: http://docs.micropython.org/en/v1.17/library/machine.html#machine.time_pulse_us
            if pulse_time < 0:
                MAX_RANGE_IN_CM = const(500) # it's really ~400 but I've read people say they see it working up to ~460
                pulse_time = int(MAX_RANGE_IN_CM * 29.1) # 1cm each 29.1us
            return pulse_time
        except OSError as ex:
            if ex.args[0] == 110: # 110 = ETIMEDOUT
                raise OSError('Out of range')
            raise ex

    def distance_mm(self):
        """
        Get the distance in milimeters without floating point operations.
        """
        pulse_time = self._send_pulse_and_wait()

        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.34320 mm/us that is 1mm each 2.91us
        # pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582 
        mm = (self.sound_speed * pulse_time) // 2        
        return mm

    def distance_cm(self):
        """
        Get the distance in centimeters with floating point operations.
        It returns a float
        """
        # To calculate the distance we get the pulse_time and divide it by 2 
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.034320 cm/us that is 1cm each 29.1us
        
        return self.distance_mm() / 10
