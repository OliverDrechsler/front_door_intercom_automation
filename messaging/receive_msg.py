from __future__ import annotations
from common.config_util import Configuration
from door import opener
from camera import blink_cam, picam, cam_common
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


logger = logging.getLogger("telegram thread")


def force_independent_connection(req, **user_kw):
    return None


telepot.api._pools = {
    "default": urllib3.PoolManager(num_pools=3, maxsize=10, retries=9,
                                   timeout=30),
}
telepot.api._which_pool = force_independent_connection


class TelegramMessages(Configuration):
    """Telegram receive messages class"""

    def __init__(
        self, bot: object, blink_instance: object, blink_auth_instance: object
    ) -> None:
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
        self.logger = logging.getLogger("fdia_telegram")
        self.logger.debug("reading config")
        self.bot = bot
        self.blink = blink_instance
        self.auth = blink_auth_instance
        self.blink_json_data = {}
        self.switch_actions = {
            "foto": "self.rcv_msg_foto",
            "blink": "self.rcv_msg_blink",
            "blinkcam": "self.rcv_msg_blinkcam",
            "picam": "self.rcv_msg_picam",
        }

    def handle_received_message(self, msg: dict) -> bool:
        """
        Handles all received telegram chat group messages

        :param msg: telegram received message dictionary
        :type msg: dict
        :return: success status
        :rtype: boolean
        """
        self.logger.info("received a telegram message")
        (self.content_type, self.chat_type, self.chat_id) = telepot.glance(msg)
        self.logger.debug(
            f"receiving a message {self.content_type}" +
            f" in chat id {self.chat_id}"
        )

        check_result = self.check_received_msg_is_text(msg)
        if (check_result):
            result = self.switch_condition(self.text.lower())
            return bool(result)
        
        return check_result

    def switch_condition(self, given_string, default="self.no_match"):
        """Received message text switch case action

        :param given_string: given text message
        :type given_string: str
        :param default: default action for no match
        :type default: str
        :return: boolean
        :rtype: bool
        """
        for key in self.switch_actions.keys():
            if key in given_string:
                self.logger.debug(f"search_key: {key} in message: " +
                                  f"{given_string}")
                result = eval(self.switch_actions.get(key) + "()")
                return bool(result)
        result = eval(default + "()")
        return bool(result)

    def rcv_msg_foto(self) -> bool:
        """
        foto switch case condition detect from received message

        :return: boolean
        :rtype: bool
        """
        self.logger.debug("text match foto found")
        return self.request_foto()

    def rcv_msg_blink(self) -> bool:
        """
        take foto switch case condition detect from received message

        :return: boolean
        :rtype: bool
        """
        self.logger.debug("text match blink found")
        return self.request_add_blink_2FA()

    def rcv_msg_blinkcam(self) -> bool:
        """
        take blinkcam switch case condition detect from received message

        :return: boolean
        :rtype: bool
        """
        self.logger.debug("text match blink cam foto found")
        return cam_common.blink_take_photo(self.auth, self.blink, self)

    def rcv_msg_picam(self) -> bool:
        """
        take picam switch case condition detect from received message

        :return: boolean
        :rtype: bool
        """
        self.logger.debug("text match PiCam foto found")
        return cam_common.picam_take_photo(self.auth, self.blink, self)

    def no_match(self) -> bool:
        """
        no mactch - default - check for TOTP code switch case condition
        detect from received message

        :return: boolean
        :rtype: bool
        """
        self.logger.debug("text not matched checking for totp code")
        return self.check_received_msg_has_code_number()

    def check_received_msg_is_text(self, msg: dict) -> bool:
        """Check received message is text and subsequent checks

        :param msg: telegram received message dictionary
        :type msg: dict
        :return: success boolean
        :rtype: bool
        """
        if self.content_type == "text":
            self.logger.info(f"received message = {msg['text']}")
            self.from_name = msg["from"]["first_name"]
            self.from_id = msg["from"]["id"]
            self.text = msg["text"]
            return self.check_chat_id()
        
        self.logger.info("received message is NOT a text message")
        return False

    def check_chat_id(self) -> bool:
        """check if chat_id from received message matches configured one

        :return: success boolean
        :rtype: bool
        """
        if str(self.chat_id) == str(self.telegram_chat_nr):
            self.logger.info(
                "chat msg allowed: chat_group_id " + str(self.chat_id) +
                " is in config"
            )
            return self.check_from_id()

        self.logger.info(
            "chat msg denied: chat_id " + str(self.chat_id) +
            " is not in config"
        )
        return False

    def check_from_id(self) -> bool:
        """check if from_id from received message matches configured one

        :return: success boolean
        :rtype: bool
        """
        if str(self.from_id) in self.allowed_user_ids:
            self.logger.info(
                "chat msg allowed: user "
                + self.from_name
                + " with from_id "
                + str(self.from_id)
                + " is in config"
            )
            return True

        self.logger.info(
            "chat msg denied: from user "
            + self.from_name
            + " with from_id "
            + str(self.from_id)
            + " is NOT in config"
        )
        return False

    def request_foto(self) -> bool:
        """
        Received request to take a foto.

        :return: 
        :rtype: bool
        """
        logger.debug("Foto request received")
        result = send_msg.telegram_send_message(
            self.bot, self.telegram_chat_nr, "I will send a foto!"
        )

        cam_common.choose_camera(self.auth, self.blink, self)
        return bool(result)

    def request_add_blink_2FA(self) -> bool:
        """
        received request to add blink cam 2FA authentication code

        :return: success status
        :rtype: boolean
        """
        match = re.search(r"(?<=^blink.)\d{6}", self.text, re.IGNORECASE)
        if match:
            self.logger.info("blink token received - will save config")
            send_msg.telegram_send_message(
                self.bot,
                self.telegram_chat_nr,
                "Blink token received " + match.group(0),
            )
            blink_cam.add_2fa_blink_token(
                token=match.group(0), blink=self.blink, auth=self.auth
            )
            blink_cam.blink_compare_config(self.auth, self.blink, self)
            return True

        self.logger.debug("no blink token detected")
        return False

    def check_received_msg_has_code_number(self) -> bool:
        """
        Check received message has a code

        :return: success status
        :rtype: boolean
        """
        bracket1 = "{"
        bracket2 = "}"
        regex_search = r"^\d{0}{1}{2}$".format(bracket1, self.otp_length,
                                               bracket2)
        self.logger.debug("regex search string")
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
            self.hash_type,
        ):
            self.logger.info(self.text + " TOTP code correct")
            send_msg.telegram_send_message(
                self.bot, self.telegram_chat_nr, "Code accepted."
            )

            opener.open_door(self.door_summer, self.run_on_raspberry)
            self.logger.info("Door opened for 5 Sec.")
            return True

        else:
            self.logger.info("wrong totp code received " + self.text)
            send_msg.telegram_send_message(
                self.bot, self.telegram_chat_nr, "TOTP code is wrong"
            )
            return False
