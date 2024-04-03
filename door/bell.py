from __future__ import annotations

# from gpiozero.input_devices import Button
from config.config_util import Configuration
from door import detect_rpi
from bot import send_msg
from camera import cam_common
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
import telebot
import logging
import time

try:
    from gpiozero import Button
except Exception:
    pass

from datetime import datetime

config = Configuration()

logger: logging.Logger = logging.getLogger(name="door-bell")


class Door(Configuration):
    """Front door subclass of configuration config watches the door bell and
        triggers
       sends telegram message and camera photo.
    """

    def __init__(
        self, bot: object, blink: Blink, auth: Auth
    ) -> None:
        """
        Initial class definition.
        
        Reads from parent class config.yaml file its configuration into class
        attribute config dict and from there into multiple attributes.
        :param bot: telegram bot class instance
        :type telebot.TeleBot: class object
        :param blink: blink class instance object
        :type Blink: class object
        :param auth: auth class instance object
        :type Auth: class object
        :return: Nothing adds class instance attribues
        :rtype: None
        """
        Configuration.__init__(self=self)
        self.logger: logging.Logger = logging.getLogger(name="door-bell")
        self.logger.debug(msg="reading config")
        self.bot: telebot.TeleBot = bot
        self.blink: Blink = blink
        self.auth: Auth = auth

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
        self.logger.info(msg="start monitoring door bell")
        if detect_rpi.detect_rpi(run_on_raspberry=self.run_on_raspberry):
            self.logger.debug(msg="RPI: start endless loop doorbell monitoring")
            button: Button = Button(pin=self.door_bell)
            while True:
                time.sleep(0.001)
                if button.is_pressed:
                    self.logger.info(msg="Door bell ringing")
                    now: str = datetime.now().strftime(format="%Y-%m-%d_%H:%M:%S")
                    send_msg.telegram_send_message(
                        self.bot, self.telegram_chat_nr, "Ding Dong! " + now
                    )
                    cam_common.choose_camera(self.auth, self.blink, self)
                    time.sleep(5)
                if test:
                    break
        else:
            self.logger.debug(msg="NOT on RPI: start empty endless loop")
            while True:
                time.sleep(60)
                if test:
                    break
