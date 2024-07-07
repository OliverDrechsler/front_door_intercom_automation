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

from datetime import datetime

logger: logging.Logger = logging.getLogger(name="door-bell")


class DoorBell():
    """Front door subclass of configuration config watches the door bell and
        triggers
       sends telegram message and camera photo.
    """

    def __init__(
            self,
            config: config_util.Configuration,
            loop,
            message_task_queue: queue.Queue,
            camera_task_queue_async: asyncio.Queue
    ) -> None:
        """
        Initial class definition.
        
        Reads from parent class config.yaml file its configuration into class
        attribute config dict and from there into multiple attributes.
        """
        self.logger: logging.Logger = logging.getLogger(name="door-bell")
        self.logger.debug(msg="reading config")
        self.config: config_util.Configuration = config
        self.loop = loop
        self.message_task_queue: queue.Queue = message_task_queue
        self.camera_task_queue_async: asyncio.Queue = camera_task_queue_async

    def ring(self, test=False) -> None:
        """
        Endless watch loop for door bell ring.

        :param test: define code test mode
        :type test: boolean
        :return: Nothing
        :rtype: None
        """
        self.logger.info(msg="start monitoring door bell")
        if detect_rpi.detect_rpi(run_on_raspberry=self.config.run_on_raspberry):
            self.logger.debug(msg="RPI: start endless loop doorbell monitoring")
            button: Button = Button(pin=self.door_bell)
            while True:
                try:
                    time.sleep(0.001)
                    if button.is_pressed:
                        self.logger.info(msg="Door bell ringing")
                        now: str = datetime.now().strftime(format="%Y-%m-%d_%H:%M:%S")
                        self.message_task_queue.put(Message_Task(send=True,
                                                                 chat_id=self.config.telegram_chat_nr,
                                                                 data_text="Ding Dong! " + now
                                                                 ))
                        asyncio.set_event_loop(self.loop)
                        asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                            Camera_Task(
                                photo=True
                            )
                        ),
                            self.loop)
                except Exception as err:
                    self.logger.error("Error: {0}".format(err))
                    pass
        else:
            self.logger.debug(msg="NOT on RPI: start empty endless loop")
            while True:
                time.sleep(60)
                if test:
                    break
