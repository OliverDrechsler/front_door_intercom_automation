try:
    import RPi.GPIO as GPIO
except:
    pass
import logging
import time

logger = logging.getLogger('door-opener')

def open_door(door_opener_port):

    logger.info("opening the door")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(door_opener_port, GPIO.OUT)
    GPIO.output(door_opener_port, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(door_opener_port, GPIO.LOW)
