import logging
import time
from door import detect_rpi
try:
    import RPi.GPIO as GPIO
except Exception:
    pass

logger: logging.Logger = logging.getLogger(name="door-opener")


def open_door(door_opener_port: int, run_on_raspberry: bool) -> bool:
    """Put Raspberry Pi GPIO port on high - voltage

    :param door_opener_port: RPi GPIO Port Number
    :type door_opener_port: int
    :param run_on_raspberry: if code runs on a RPi, defaults to True
    :type run_on_raspberry: bool
    :return: success status
    :rtype: boolean
    """
    if detect_rpi.detect_rpi(run_on_raspberry=run_on_raspberry):
        logger.info(msg="opening the door")
        GPIO.setmode(mode=GPIO.BCM)
        GPIO.setup(channel=door_opener_port, dir=GPIO.OUT)
        GPIO.output(channel=door_opener_port, state=GPIO.HIGH)
        time.sleep(5)
        GPIO.output(channel=door_opener_port, state=GPIO.LOW)
        return True
    else:
        logger.info(msg="not running on raspberry pi - will not open the door")
        return False
