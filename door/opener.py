from __future__ import annotations
try:
    import RPi.GPIO as GPIO
except:
    pass
import logging
import time

logger = logging.getLogger('door-opener')

def open_door(door_opener_port: int, run_on_raspberry: bool) -> None:
    """Put Raspberry Pi GPIO port on high - voltage

    :param door_opener_port: RPi GPIO Port Number
    :type door_opener_port: int
    :param run_on_raspberry: if code runs on a RPi, defaults to True
    :type run_on_raspberry: bool
    :return: Nothing
    :rtype: None
    """
    if run_on_raspberry:
        logger.info("opening the door")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(door_opener_port, GPIO.OUT)
        GPIO.output(door_opener_port, GPIO.HIGH)
        time.sleep(5)
        GPIO.output(door_opener_port, GPIO.LOW)
    else:
        logger.info("not running on raspberry pi - will not open the door")
