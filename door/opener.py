import logging
import queue
import threading
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
    def __init__(self, shutdown_event: threading.Event, config: config_util.Configuration, loop,
                 message_task_queue: queue.Queue, door_open_task_queue: queue.Queue) -> None:
        """
        A constructor method for initializing the DoorOpener class with the provided parameters.

        Parameters:
            shutdown_event (threading.Event): An event to signal the shutdown of operations.
            config (config_util.Configuration): The configuration object for the DoorOpener.
            loop: The loop object for the DoorOpener.
            message_task_queue (queue.Queue): A queue for message tasks.
            door_open_task_queue (queue.Queue): A queue for door open tasks.

        Returns:
            None
        """
        self.logger: logging.Logger = logging.getLogger(name="door-opener")
        self.logger.debug(msg="reading config")
        self.shutdown_event: threading.Event = shutdown_event
        self.config: config_util.Configuration = config
        self.loop = loop
        self.message_task_queue: queue.Queue = message_task_queue
        self.door_open_task_queue: queue.Queue = door_open_task_queue

    def start(self):
        """
        Starts the thread endless loop to open the door.

        This method runs in an infinite loop until the `shutdown_event` is set. It continuously retrieves tasks from the `door_open_task_queue` and processes them. If a task is an instance of `Open_Door_Task`, it performs the following actions based on the task attributes:
        - If `task.open` is True, it logs the received task and opens the door by calling the `open_door` method.
        - If `task.reply` is True and `task.message` is not None, it puts a `Message_Task` object with the reply flag set to True, the chat ID from the task, the message from the task, and the data text "Door opened!" into the `message_task_queue`.
        - If `task.reply` is False, it puts a `Message_Task` object with the send flag set to True, the chat ID from the configuration, and the data text "Door opened!" into the `message_task_queue`.
        - If an exception occurs during the execution of the loop, it logs the error and continues.

        Parameters:
            None

        Returns:
            None
        """
        self.logger.info(msg="thread endless loop open door")
        while not self.shutdown_event.is_set():
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
                            self.message_task_queue.put(
                                Message_Task(reply=True, chat_id=task.chat_id, message=task.message,
                                             data_text="Door opened!"))
                        else:
                            self.message_task_queue.put(
                                Message_Task(send=True, chat_id=self.config.telegram_chat_nr, data_text="Door opened!"))
                time.sleep(0.1)
            except Exception as err:
                self.logger.error("Error: {0}".format(err))
                pass
        self.logger.info(msg="stop endless loop door opener")

    def open_door(self) -> bool:
        """
        A function that opens the door based on Raspberry Pi detection.

        Parameters:
            self: The object instance.

        Returns:
            bool: True if the door is successfully opened, False otherwise.
        """
        if detect_rpi.detect_rpi(run_on_raspberry=self.config.run_on_raspberry):
            logger.info(msg="opening the door")
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.config.door_summer, GPIO.OUT)
            GPIO.output(self.config.door_summer, GPIO.HIGH)
            time.sleep(5)
            GPIO.output(self.config.door_summer, GPIO.LOW)
            return True
        else:
            logger.info(msg="not running on raspberry pi - will not open the door")
            return False
