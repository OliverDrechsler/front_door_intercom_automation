import logging
import queue
import time

from door import detect_rpi

try:
    import RPi.GPIO as GPIO
except Exception:
    pass
from config import config_util
from config.data_class import Open_Door_Task, Message_Task

logger: logging.Logger = logging.getLogger(name="door-opener")


class DoorOpener():
    def __init__(self, config: config_util.Configuration, loop, message_task_queue: queue.Queue,
                 door_open_task_queue: queue.Queue) -> None:
        """
        Initial class definition.
        """
        self.logger: logging.Logger = logging.getLogger(name="door-opener")
        self.logger.debug(msg="reading config")
        self.config: config_util.Configuration = config
        self.loop = loop
        self.message_task_queue: queue.Queue = message_task_queue
        self.door_open_task_queue: queue.Queue = door_open_task_queue

    def start(self):
        self.logger.info(msg="thread endless loop open door")
        while True:
            try:
                task = self.door_open_task_queue.get()
                if task is None:  # Exit signal
                    break
                self.logger.info(f"received task: {task}")
                if isinstance(task, Open_Door_Task):
                    if (task.open):
                        self.logger.info(f"Processing open door: {task}")
                        self.open_door()
                        if (task.reply and task.message is not None):
                            self.message_task_queue.put(Message_Task(reply=True,
                                                                     chat_id=task.chat_id,
                                                                     message=task.message,
                                                                     data_text="Door opened!"
                                                                     ))
                        else:
                            self.message_task_queue.put(Message_Task(send=True,
                                                                     chat_id=self.config.telegram_chat_nr,
                                                                     data_text="Door opened!"
                                                                     ))
                time.sleep(0.1)
            except Exception as err:
                self.logger.error("Error: {0}".format(err))
                pass

    def open_door(self) -> bool:
        """Put Raspberry Pi GPIO port on high - voltage
        :return: success status
        :rtype: boolean
        """
        if detect_rpi.detect_rpi(run_on_raspberry=self.config.run_on_raspberry):
            logger.info(msg="opening the door")
            GPIO.setmode(mode=GPIO.BCM)
            GPIO.setup(channel=self.config.door_summer, dir=GPIO.OUT)
            GPIO.output(channel=self.config.door_summer, state=GPIO.HIGH)
            time.sleep(5)
            GPIO.output(channel=self.config.door_summer, state=GPIO.LOW)
            return True
        else:
            logger.info(msg="not running on raspberry pi - will not open the door")
            return False
