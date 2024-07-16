from __future__ import annotations
import asyncio
try:
    from gpiozero import Button
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
        if detect_rpi.detect_rpi(run_on_raspberry=self.config.run_on_raspberry):
            self.logger.debug(msg="RPI: start endless loop doorbell monitoring")
            button: Button = Button(pin=self.config.door_bell_pin)
            while not self.shutdown_event.is_set():
                try:
                    time.sleep(0.001)
                    if button.is_pressed:
                        self.logger.info(msg="Door bell ringing")
                        now: str = datetime.now().strftime(format="%Y-%m-%d_%H:%M:%S")
                        self.message_task_queue.put(Message_Task(send=True, chat_id=self.config.telegram_chat_nr,
                                                                 data_text="Ding Dong! " + now))
                        asyncio.set_event_loop(self.loop)
                        asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(Camera_Task(photo=True)),
                            self.loop)
                except Exception as err:
                    self.logger.error("Error: {0}".format(err))
                    pass
            self.logger.info(msg="stop endless loop doorbell monitoring")
        else:
            self.logger.debug(msg="NOT on RPI: do a ring in 10 sec and stop afterwards.")
            time.sleep(10)
            now: str = datetime.now().strftime(format="%Y-%m-%d_%H:%M:%S")
            self.message_task_queue.put(Message_Task(send=True, chat_id=self.config.telegram_chat_nr,
                                                     data_text="Ding Dong! " + now))
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(Camera_Task(photo=True)),
                                             self.loop)

            self.logger.info(msg="STOP: not on RPI - endless door bell loop stopped")
