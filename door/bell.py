from __future__ import annotations
from common.config_util import Configuration
from camera import blink_cam, picam, cam_common
from messaging import send_msg
import logging
import time
import json
try:
    from gpiozero import Button
except:
    pass

import datetime
config = Configuration()

logger = logging.getLogger('door-bell')

class Door(Configuration):
    """Front door subclass of configuration config watches the door bell and triggers
       sends telegram message and camera photo.
    """

    def __init__(self, bot: object, blink_instance: object, blink_auth_instance: object) -> None:
        """
        Initial class definition.
        
        Reads from parent class config.yaml file its configuration into class attribute
        config dict and from there into multiple attributes.
        :param blink_instance: blink class instance object
        :type blink_instance: class object
        :param telegram_instance: telegram bot class instance
        :type telegram_instance: class object
        :return: Nothing adds class instance attribues
        :rtype: None
        """
        Configuration.__init__(self)
        self.logger = logging.getLogger('door-bell')
        self.logger.debug("reading config")
        self.bot = bot
        self.blink = blink_instance
        self.auth = blink_auth_instance

    def ring(self, test=False) -> None:
        """
        Endless watch loop for door bell ring.

        :param self.door_bell: class attribute door_bell_port
        :type self.door_bell: int
        :param test: define code test mode
        :type test: boolean
        :param self.telegram_token:
        :param self.telegram_chat_nr:
        :return: Nothing
        :rtype: None
        """
        self.logger.info("start monitoring door bell")
        if self.run_on_raspberry:
            self.logger.debug("RPI: start endless loop doorbell monitoring")
            button = Button(self.door_bell)
            while True:
                time.sleep(0.001)
                if button.is_pressed:
                    self.logger.info("Door bell ringing")
                    send_msg.telegram_send_message(
                        self.bot,
                        self.telegram_chat_nr,
                        "Ding Dong!" +
                        str(datetime.datetime.now()))
                    cam_common.choose_camera(self.auth, self.blink, self)
                    time.sleep(5)
                if test:
                    break
        else:
            self.logger.debug("NOT on RPI: start empty endless loop")
            while True:
                time.sleep(60)
                if test:
                    break
