#!/usr/bin/python

import time
import base64
import json
import os
import sys
import threading
#import paho.mqtt.client as mqtt
import paho.mqtt.publish as mqtt
import Adafruit_MPR121.MPR121 as MPR121
import RPi.GPIO as GPIO

thingName = "Pi3_" + os.getenv("RESIN_DEVICE_UUID")

def control_relay(gpio, delay_to_close):
    GPIO.output(gpio, GPIO.HIGH)
    print('{0} gpio for relay opened'.format(gpio))
    time.sleep(delay_to_close)
    GPIO.output(gpio, GPIO.LOW)
    print('{0} gpio for relay closed'.format(gpio))
    return

def control_flash_relay(gpio, times=10, duration_on=0.5, duration_off=0.5):
    for i in range(times):
        GPIO.output(gpio, GPIO.HIGH)
        print('{0} gpio for flash relay opened'.format(gpio))
        time.sleep(duration_on)
        GPIO.output(gpio, GPIO.LOW)
        print('{0} gpio for flash relay closed'.format(gpio))
        time.sleep(duration_off)
    return

# Create MPR121 instance.
cap = MPR121.MPR121()

if not cap.begin():
    print('Error initializing MPR121. Check your wiring!')
    sys.exit(1)

# relay setup
relay_1 = 23    
relay_2 = 24 
relay_3 = 25 

GPIO.setmode(GPIO.BCM)
GPIO.setup(relay_1, GPIO.OUT)
GPIO.setup(relay_2, GPIO.OUT)
GPIO.setup(relay_3, GPIO.OUT)

# Callback fires when conected to MQTT broker.
# def on_connect(client, userdata, flags, rc):
#     print('Connected with result code {0}'.format(rc))
    # Subscribe (or renew if reconnect).

# Callback fires when a published message is received.
# def on_message(client, userdata, msg):

# client = mqtt.Client(thingName)
# client.on_connect = on_connect  # Specify on_connect callback
# client.on_message = on_message  # Specify on_message callback
# client.connect('localhost', 1883, 60)  # Connect to MQTT broker (also running on Pi).

last_touched = cap.touched()

try:
    while True:
        # client.loop_start()
        current_touched = cap.touched()
        # Check each pin's last and current state to see if it was pressed or released.
        for i in range(12):
            # Each pin is represented by a bit in the touched value.  A value of 1
            # means the pin is being touched, and 0 means it is not being touched.
            pin_bit = 1 << i
            # First check if transitioned from not touched to touched.
            if current_touched & pin_bit and not last_touched & pin_bit:
                print('{0} touched!'.format(i))
                if i == 0:
                    t0 = threading.Thread(target=control_flash_relay, args=(relay_1, 10, 0.2, 0.2))
                    t0.start()
                if i == 1:
                    t1 = threading.Thread(target=control_relay, args=(relay_2, 5))
                    t1.start()
                if i == 2:
                    t2 = threading.Thread(target=control_relay, args=(relay_3, 5))
                    t2.start()
                if i in (3, 4, 5):
                    if i == 3:
                        channel = 'red'
                    elif i == 4:        
                        channel = 'green'
                    elif i == 5:        
                        channel = 'blue'
                    data = {"state": {"reported": {"channel": channel, "status": 1}}}
                    print(data) 
                    # client.publish("led", json.dumps(data))
                    mqtt.single("rxpboard/hat", json.dumps(data), hostname="localhost")

            # Next check if transitioned from touched to not touched.
            if not current_touched & pin_bit and last_touched & pin_bit:
                print('{0} released!'.format(i))
        # Update last state and wait a short period before repeating.
        last_touched = current_touched
        time.sleep(0.1)
        # client.loop_stop()
        
except KeyboardInterrupt:
    # here you put any code you want to run before the program 
    # exits when you press CTRL+C
    print "exited"

except:
    # this catches ALL other exceptions including errors.
    # You won't get any error messages for debugging
    # so only use it once your code is working
    print "Other error or exception occurred!"

finally:
    GPIO.cleanup() # this ensures a clean exit