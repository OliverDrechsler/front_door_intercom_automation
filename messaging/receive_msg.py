from __future__ import annotations
from common.config_util import Configuration
from door import opener
from camera import blink_cam, picam
from . import otp
from . import send_msg
from pprint import pprint
from telepot.loop import MessageLoop
import telepot
import logging
import re
import os
import time
import urllib3
import json


logger = logging.getLogger('fdia_telegram')

def force_independent_connection(req, **user_kw):
    return None

telepot.api._pools = {'default': urllib3.PoolManager(
    num_pools=3, maxsize=10, retries=9, timeout=30), }
telepot.api._which_pool = force_independent_connection



class TelegramMessages(Configuration):
    """Telegram receive messages class"""

    def __init__(self, bot: object, blink_instance: object, blink_auth_instance: object) -> None:
        """
        Initial Telegram receive class instance setup

        :param bot: Telegram bot class instance object
        :type bot: object
        :param blink_instance: blink cam class instance object
        :type blink_instance: object
        :param blink_auth_instance: blink cam auth class instance object
        :type blink_auth_instance: object
        """
        self.logger = logging.getLogger('fdia_telegram')
        self.logger.info("reading config")
        Configuration.__init__(self)
        self.bot = bot
        self.blink = blink_instance
        self.auth = blink_auth_instance
        self.blink_json_data = {}

    def handle_received_message(self, msg: dict) -> None:
        """
        Handles all received telegram chat group messages

        :param msg: telegram received message dictionary
        :type msg: dict
        """
        self.logger.info("handle_received_message")
        (self.content_type, 
         self.chat_type, 
         self.chat_id) = telepot.glance(msg)

        if self.content_type == 'text':
            self.from_name = msg['from']['first_name']
            self.from_id = msg['from']['id']
            self.text = msg['text']

            if str(self.chat_id) == str(self.telegram_chat_nr):

                if str(self.from_id) in self.allowed_user_ids:
                    if "foto" in self.text.lower():
                        logger.info(
                            "Foto request received")
                        send_msg.telegram_send_message(self.bot, 
                            self.telegram_chat_nr, 
                            "ich werde ein foto senden")
                        try:
                            # request_take_foto()
                            # request_download_foto()
                            self.logger.info("take a snapshot")
                            blink_cam.blink_snapshot(self.blink, 
                                self.blink_name, 
                                self.common_image_path)
                            
                            self.blink_json_load()
                            is_equal = self.auth.login_attributes == self.blink_json_data
                            if not is_equal:
                                self.logger.debug("blink config json dict differs from running config")
                                self.logger.debug("blink config object dict = {0}".format(self.auth.login_attributes))
                                self.logger.debug("blink config file = {0}".format(self.blink_json_data))
                                blink_cam.save_blink_config(
                                    self.blink, 
                                    self.blink_config_file)
                            else:
                                self.logger.debug("blink config json object is same as in config file")

                            self.logger.info("send snapshot photo")
                            send_msg.telegram_send_photo(
                                self.bot, 
                                self.telegram_chat_nr, 
                                self.common_image_path)
                        except:
                            self.logger.info("take snapshot error occured")
                            pass

                    elif "blink" in self.text.lower():
                        match = re.search("(?<=^blink.)\d{6}", self.text, re.IGNORECASE)
                        if match:
                            blink_cam.add_2fa_blink_token(
                                token=match.group(0), 
                                blink=self.blink, 
                                auth=self.auth)
                            
                            self.blink_json_load()
                            is_equal = self.auth.login_attributes == self.blink_json_data
                            if not is_equal:
                                self.logger.debug("blink config json dict differs from running config")
                                self.logger.debug("blink config object dict = {0}".format(self.auth.login_attributes))
                                self.logger.debug("blink config file = {0}".format(self.blink_json_data))
                                blink_cam.save_blink_config(
                                    self.blink, 
                                    self.blink_config_file)
                            else:
                                self.logger.debug("blink config json object is same as in config file")

                        send_msg.telegram_send_message(
                            self.bot, 
                            self.telegram_chat_nr, 
                            "Blink token received " + match.group(0))

                    # elif otp.verify_otp(self.text, self.otp_password, self.otp_length, self.otp_interval):
                    elif otp.verify_otp(
                            self.text, 
                            self.otp_password, 
                            self.otp_length, 
                            self.otp_interval):
                        self.logger.info(
                            "correct password received " + self.text)
                        send_msg.telegram_send_message(
                            self.bot, 
                            self.telegram_chat_nr, 
                            "Passwort ist richtig. Ich öffne die Tür")
                        if self.is_raspberry_pi:
                            opener.open_door(self.door_summer)
                            self.logger.info(
                                "Door opened for 5 Sec. ")
                        else:
                            self.logger.info("do not open door because no Raspberry Pi detected"

                    else:
                        send_msg.telegram_send_message(
                            self.bot, 
                            self.telegram_chat_nr, 
                            "Passwort ist falsch")
                        self.logger.info(
                            "wrong password / text received " + self.text)
                else:
                    self.logger.info(
                        "from_id " + str(self.from_id) +
                        " from user " + self.from_name + " not allowed in config")
            else:
                self.logger.info(
                    "chat_id " + str(self.chat_id) +
                    " not allowed in config")

    def blink_json_load(self) -> None:
        """Load blink json credentials from file."""
        try:
            with open(self.blink_config_file, "r") as json_file:
                self.blink_json_data = json.load(json_file)
        except FileNotFoundError:
            self.logger.error("Could not find %s", self.blink_config_file)
        except json.decoder.JSONDecodeError:
            self.logger.error("File %s has improperly formatted json", self.blink_config_file)
        return None

