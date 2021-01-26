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
        Configuration.__init__(self)
        self.logger = logging.getLogger('fdia_telegram')
        self.logger.info("reading config")
        self.bot = bot
        self.blink = blink_instance
        self.auth = blink_auth_instance
        self.blink_json_data = {}

    def handle_received_message(self, msg: dict) -> bool:
        """
        Handles all received telegram chat group messages

        :param msg: telegram received message dictionary
        :type msg: dict
        :return: success status
        :rtype: boolean
        """
        (self.content_type, 
         self.chat_type, 
         self.chat_id) = telepot.glance(msg)
        self.logger.debug(f"receiving a message {self.content_type} in chat id {self.chat_id}")

        if self.content_type == 'text':
            self.logger.info(f"received message = {msg['text']}")
            self.from_name = msg['from']['first_name']
            self.from_id = msg['from']['id']
            self.text = msg['text']
        else:
            self.logger.info(f"received message is NOT a text message")
            return False
        
        if str(self.chat_id) == str(self.telegram_chat_nr):
            self.logger.info(
                "allowed: chat_id " + str(self.chat_id) +
                " in config")
        else:
            self.logger.info(
                "denied: chat_id " + str(self.chat_id) +
                " not in config")
            return False
    
        if str(self.from_id) in self.allowed_user_ids:
            self.logger.info(
                "allowed: from_id " + str(self.from_id) +
                " & from user " + self.from_name + " is in config")        
        else:
            self.logger.info(
                "denied: from_id " + str(self.from_id) +
                " & from user " + self.from_name + " is NOT in config")
            return False

        if "foto" in self.text.lower():
            self.request_foto()
            return True
        elif "blink" in self.text.lower():
            self.request_add_blink_2FA()
            return True
        else: 
            self.check_received_msg_has_code_number()
            return True
        
        return False
        
    def blink_json_load(self) -> bool:
        """Load blink json credentials from file.
        
        :return: success status
        :rtype: boolean
        """
        try:
            with open(self.blink_config_file, "r") as json_file:
                self.blink_json_data = json.load(json_file)
            return True
        except FileNotFoundError:
            self.logger.error("Could not find %s", self.blink_config_file)
        except json.decoder.JSONDecodeError:
            self.logger.error("File %s has improperly formatted json", self.blink_config_file)
        return False

    def blink_compare_config(self) -> bool:
        """
        Compares Blink actual class config with blink config file
        and stores it in case of difference.
        Blink will daily update the device token.
        Therefore we have to update the config file

        :return: success status
        :rtype: boolean
        """
        self.blink_json_load()
        if self.auth.login_attributes != self.blink_json_data:
            self.logger.debug("saved blink config file differs from running config")
            self.logger.debug("blink config object = {0}".format(self.auth.login_attributes))
            self.logger.debug("blink config file   = {0}".format(self.blink_json_data))
            blink_cam.save_blink_config(
                self.blink, 
                self.blink_config_file)
            return True
        else:
            self.logger.debug("saved blink config file == running config")
            return False

    def request_foto(self) -> bool:
        """
        Received request to take a foto.

        :return: success status
        :rtype: boolean
        """
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
            self.blink_compare_config()
            self.logger.info("send snapshot photo")
            send_msg.telegram_send_photo(
                self.bot, 
                self.telegram_chat_nr, 
                self.common_image_path)
            return True
        except:
            self.logger.info("take snapshot error occured")
            return False


    def request_add_blink_2FA(self) -> bool:
        """
        received request to add blink cam 2FA authentication code

        :return: success status
        :rtype: boolean
        """
        match = re.search("(?<=^blink.)\d{6}", self.text, re.IGNORECASE)
        send_msg.telegram_send_message(
            self.bot, 
            self.telegram_chat_nr, 
            "Blink token received " + match.group(0))

        if match:
            blink_cam.add_2fa_blink_token(
                token=match.group(0), 
                blink=self.blink, 
                auth=self.auth)
            self.blink_compare_config()
            return True

        return False
    
    def check_received_msg_has_code_number(self) -> bool:
        """
        Check received message has a code 

        :return: success status
        :rtype: boolean
        """
        bracket1 = "{"
        bracket2 = "}"
        regex_search = "^\d{0}{1}{2}$".format(bracket1, self.otp_length, bracket2)
        self.logger.debug(f"regex search string {regex_search}")
        match = re.search(regex_search, self.text, re.IGNORECASE)
        if match:
            self.verify_totp_code_in_msg()
            return True

        self.logger.debug("no code number detected")
        return False

    def verify_totp_code_in_msg(self) -> bool:
        """
        Verify msg text code if it matches totp code

        :return: success status
        :rtype: boolean
        """
        if otp.verify_totp_code(
                self.text, 
                self.otp_password, 
                self.otp_length, 
                self.otp_interval,
                self.hash_type):
            self.logger.info(
                "correct password received " + self.text)
            send_msg.telegram_send_message(
                self.bot, 
                self.telegram_chat_nr, 
                "Passwort ist richtig. Ich öffne die Tür")
            
            if self.run_on_raspberry:
                opener.open_door(self.door_summer, self.run_on_raspberry)
                self.logger.info(
                    "Door opened for 5 Sec. ")
            else:
                self.logger.info("do not open door because not running on a Raspberry Pi")
            
            return True

        else: 
            self.logger.info(
                "wrong password received " + self.text)
            send_msg.telegram_send_message(
                self.bot, 
                self.telegram_chat_nr, 
                "Passwort ist falsch")
            return False
