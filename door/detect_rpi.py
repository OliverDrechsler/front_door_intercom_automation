import io
import logging
import os

logger: logging.Logger = logging.getLogger(name="detect_rpi")


def detect_rpi(run_on_raspberry: bool) -> bool:
    """
    Detects whether the system is running on a Raspberry Pi based on the model information
    retrieved from '/sys/firmware/devicetree/base/model' or '/proc/cpuinfo'.

    Args:
        run_on_raspberry (bool): A boolean indicating whether to force the function to run on a Raspberry Pi.

    Returns:
        bool: True if a Raspberry Pi is detected, False otherwise.
    """

    if os.name != 'posix':
        logger.debug("no posix detected")
        return False

    try:
        logger.debug("try to detect rpi from /sys/firmware/devicetree/base/model now")
        with io.open('/sys/firmware/devicetree/base/model', 'r') as model:
            if 'raspberry pi' in model.read().lower():
                logger.info("RPi detected in firmware model successful")
                return True

        logger.debug("try to detect rpi after firmware detect failed now from /proc/cpuinfo")
        rpi_hw_chips = ('BCM2708', 'BCM2709', 'BCM2711', 'BCM2835', 'BCM2836')
        with io.open('/proc/cpuinfo', 'r') as cpuinfo:
            for line in cpuinfo:
                logger.debug(f"read line {line} from cpuinfo")
                if line.startswith('Hardware'):
                    logger.debug(f"detected hardware line {line}")
                    _, value = line.strip().split(sep=':', maxsplit=1)
                    value: str = value.strip()
                    logger.debug(f"hardware chip value: {value}")
                    if value.upper() in rpi_hw_chips:
                        logger.info("RPi detected in /poc/cpuinfo chips - successful")
                        return True
    except Exception:
        logger.info("no RPi detected - do not use door bell and door opener")
        pass
    logger.debug(msg="check if force run on RPi boolean is set")
    if run_on_raspberry:
        logger.info(msg="set to force to run on RPi")
        return run_on_raspberry

    return False
