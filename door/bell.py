from __future__ import annotations

import asyncio

try:
    import RPi.GPIO as GPIO
except Exception:
    pass
from config import config_util
from door import detect_rpi
from config.data_class import Message_Task, Camera_Task
import logging
import time
import queue
import threading
from datetime import datetime

logger: logging.Logger = logging.getLogger(name="door-bell")

class DoorBell():
    """
        Front door subclass of configuration config watches the door bell and
        triggers sends telegram message and camera photo.
    """

    def __init__(self, shutdown_event: threading.Event, config: config_util.Configuration, loop,
                 message_task_queue: queue.Queue, camera_task_queue_async: asyncio.Queue) -> None:
        """
        Initializes a new instance of the `DoorBell` class.

        Args:
            shutdown_event (threading.Event): An event object used to signal the shutdown of the application.
            config (config_util.Configuration): The configuration object containing the settings for the doorbell.
            loop: The event loop used for asynchronous operations.
            message_task_queue (queue.Queue): A queue used to send messages to the message task.
            camera_task_queue_async (asyncio.Queue): A queue used to send camera tasks to the camera task.

        Returns:
            None
        """
        self.logger: logging.Logger = logging.getLogger(name="door-bell")
        self.logger.debug(msg="reading config")
        self.shutdown_event: threading.Event = shutdown_event
        self.config: config_util.Configuration = config
        self.loop = loop
        self.message_task_queue: queue.Queue = message_task_queue
        self.camera_task_queue_async: asyncio.Queue = camera_task_queue_async

        # Setup GPIO
        if detect_rpi.detect_rpi(run_on_raspberry=self.config.run_on_raspberry):
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.config.door_bell, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def ring(self, test=False) -> None:
        """
        Monitors the door bell and triggers a series of actions when the bell rings.

        Args:
            test (bool, optional): If True, the function will exit after the first ring. Defaults to False.

        Returns:
            None

        Raises:
            Exception: If an error occurs during the execution of the function.

        """
        self.logger.info(msg="start monitoring door bell")
        asyncio.set_event_loop(self.loop)
        if detect_rpi.detect_rpi(run_on_raspberry=self.config.run_on_raspberry):
            self.logger.debug(msg="RPI: start endless loop doorbell monitoring")
            while not self.shutdown_event.is_set():
                try:
                    time.sleep(0.01)
                    if GPIO.input(self.config.door_bell) == GPIO.LOW:  # Button is pressed
                        self.logger.info(msg="Door bell ringing")
                        now: str = datetime.now().strftime(format="%Y-%m-%d_%H:%M:%S")
                        self.message_task_queue.put(Message_Task(send=True, chat_id=self.config.telegram_chat_nr,
                                                                 data_text="Ding Dong! " + now))
                        asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                            Camera_Task(photo=True, chat_id=self.config.telegram_chat_nr)), self.loop)
                except Exception as err:
                    self.logger.error("Error: {0}".format(err))
                    pass
            self.logger.info(msg="stop endless loop doorbell monitoring")
            GPIO.cleanup()
        else:
            # not on RPI - endless loop doorbell for testing purpose
            self.logger.info(msg="Start: not on RPI - endless door bell loop")
            self.logger.info(msg=f"NOT on RPI: do a test ring every 60 sec = {self.config.testing_bell_msg}")
            while not self.shutdown_event.is_set():
                time.sleep(60)
                if (self.config.testing_bell_msg):
                    now: str = datetime.now().strftime(format="%Y-%m-%d_%H:%M:%S")
                    self.logger.info(msg="now send door bell ring")
                    self.message_task_queue.put(
                        Message_Task(send=True, chat_id=self.config.telegram_chat_nr, data_text="Ding Dong! " + now))
                    asyncio.run_coroutine_threadsafe(
                        self.camera_task_queue_async.put(Camera_Task(photo=True, chat_id=self.config.telegram_chat_nr)),
                        self.loop)
                    # asyncio.get_event_loop().run_forever()
            self.logger.info(msg="STOP: not on RPI - endless door bell loop stopped")
