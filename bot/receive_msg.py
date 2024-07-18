from __future__ import annotations

import asyncio
import logging
import queue
import re
import threading

import pyotp
import telebot

from config import config_util
from config.data_class import Camera_Task, Open_Door_Task

logger: logging.Logger = logging.getLogger(name="receive_msg")


class ReceivingMessage():
    """Receiving Telegram Bot messages"""

    telebot.apihelper.RETRY_ON_ERROR = True

    def __init__(self, shutdown_event: threading.Event, config: config_util.Configuration, loop,
                 camera_task_queue_async: asyncio.Queue, door_open_task_queue: queue.Queue) -> None:
        """Initial class definition."""
        self.logger: logging.Logger = logging.getLogger(name="ReceivingMessage")
        self.config: config_util.Configuration = config
        self.loop = loop
        self.camera_task_queue_async: asyncio.Queue = camera_task_queue_async
        self.door_open_task_queue = door_open_task_queue
        self.logger.debug(msg="initialize receive_msg class instance")
        self.bot = self.config.bot
        foto_list: list[str] = ["foto", "Foto", "FOTO"]
        blink_list: list[str] = ["blink", "Blink", "BLINK"]
        picam_list: list[str] = ["picam", "Picam", "PICAM", "PiCam"]
        blink_auth_list: list[str] = ["blink_auth", "Blink_auth", "Blink_Auth", "BLINK_AUTH"]
        self.foto_command = self.bot.message_handler(commands=foto_list)(self._take_foto)
        self.blink_command = self.bot.message_handler(commands=blink_list)(self._take_blink_foto)
        self.picam_command = self.bot.message_handler(commands=picam_list)(self._take_picam_foto)
        self.blink_auth_command = self.bot.message_handler(commands=blink_auth_list)(self._register_bink_authentication)
        self.message_request = self.bot.message_handler(func=lambda message: message.content_type == "text")(
            self._receive_any_msg_text)

    def start(self) -> None:
        """
        Starts the bot's endless polling.
        Uses the bot's infinity_polling method with specified timeout and long_polling_timeout.
        Logs any errors that occur during polling.
        """
        self.logger.debug(msg="start bot endless polling")
        try:
            self.bot.infinity_polling(logger_level=logging.DEBUG, timeout=10, long_polling_timeout=5)
        except Exception as err:
            self.logger.error("Error: {0}".format(err))
            pass
        self.logger.info(msg="infinity_polling ended")
        self.stop()

    def stop(self):
        """
        A method to stop the bot. It logs the action of stopping bot polling, stops the bot from polling, removes the webhook, and logs the completion of stopping the bot.
        """
        self.logger.info(msg="stop bot polling")
        self.bot.stop_polling()
        self.logger.info(msg="stop bot remove webhook")
        self.bot.remove_webhook()
        self.logger.info(msg="bot stop finished")

    def _receive_any_msg_text(self, message: telebot.types.Message) -> None:
        """
        Check if the message is received from an allowed telegram chat group and allowed user ID.
        If the conditions are met, check if the message text has a TOTP code and open the door if correct, otherwise do nothing.

        Parameters:
            message (telebot.types.Message): The message object received.

        Returns:
            None
        """
        if self._get_allowed(message=message):
            # check is message text has TOTP code and if correct open door, otherwise do nothing
            self._validate_msg_text_has_code(message=message)

    def _take_foto(self, message: telebot.types.Message) -> None:
        """
        Takes a photo request from a telegram message and puts it into a camera task queue.

        Args:
            message (telebot.types.Message): The telegram message object containing the photo request.

        Returns:
            None

        This function first logs a debug message indicating that a photo request has been received with the given message.
        It then checks if the message is received from an allowed telegram chat group and if it was sent by an allowed user ID.
        If the conditions are met, it sets the event loop to the current loop and puts a camera task into the camera task queue.
        The camera task contains the chat ID, message, reply flag, and photo flag.
        """
        self.logger.debug(f"received foto request with message {message}")
        if self._get_allowed(message=message):
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(chat_id=message.chat.id, message=message, reply=True, photo=True)), self.loop)

    def _take_picam_foto(self, message: telebot.types.Message) -> None:
        """
        Takes a photo request specific to the PiCam (foto API [PiCamAPI](https://github.com/OliverDrechsler/PiCam_API)) from a telegram message and puts it into a camera task queue.

        Args:
            message (telebot.types.Message): The telegram message object containing the photo request.

        Returns:
            None
        """
        self.logger.debug(f"received /picam request with message {message}")
        if self._get_allowed(message=message):
            # start new thread for taking a foto
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(chat_id=message.chat.id, message=message, reply=True, picam_photo=True)), self.loop)

    def _take_blink_foto(self, message: telebot.types.Message) -> None:
        """
        Takes a photo request specific to the Blink camera from a telegram message and puts it into a camera task queue.

        Args:
            message (telebot.types.Message): The telegram message object containing the photo request.

        Returns:
            None

        This function first logs a debug message indicating that a Blink photo request has been received with the given message.
        It then checks if the message is received from an allowed telegram chat group and if it was sent by an allowed user ID.
        If the conditions are met, it sets the event loop to the current loop and puts a camera task into the camera task queue.
        The camera task contains the chat ID, message, reply flag, and blink_photo flag.
        """
        self.logger.debug(f"received blink request with message {message}")
        if self._get_allowed(message=message):
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(chat_id=message.chat.id, message=message, reply=True, blink_photo=True)), self.loop)

    def _register_bink_authentication(self, message: telebot.types.Message) -> None:
        """
        Registers a Blink authentication based on the received message.

        Args:
            self: the object instance
            message (telebot.types.Message): the message received

        Returns:
            None
        """
        self.logger.debug(f"received /blink_auth request with message {message}")
        if self._get_allowed(message=message):
            # start new thread for taking a foto
            self._rcv_blink_auth(message)

    def _rcv_blink_auth(self, message: telebot.types.Message) -> None:

        self.logger.debug(f"received blink token with message {message}")
        match = re.search(r'^/blink_auth (\d{6})$', message.text, re.IGNORECASE)
        if match:
            self.logger.info(msg="blink token received - will save config")
            message_text = "Blink token received " + match.group(1)
            self.bot.reply_to(message=message, text=message_text)
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(blink_mfa=match.group(1), chat_id=message.chat.id, message=message, reply=True)), self.loop)
            return

        self.logger.debug(msg="no blink token detected")
        message = "Blink token received " + match.group(1)
        self.bot.reply_to(message=message, text="no blink token detected")
        return

    def _get_allowed(self, message: telebot.types.Message) -> bool:
        """
        Checks if the message chat ID matches the configured Telegram chat number and calls get_allowed_user
        if the condition is met. Returns True if the user is allowed, False otherwise.

        Parameters:
            message (telebot.types.Message): The message object received.

        Returns:
            bool: True if the user is allowed, False otherwise.
        """
        if str(message.chat.id) == self.config.telegram_chat_nr:
            return self._get_allowed_user(message=message)
        return False

    def _get_allowed_user(self, message: telebot.types.Message) -> bool:
        """
        Checks if the message from_user ID matches the configured allowed user IDs.

        Parameters:
            message (telebot.types.Message): The message object received.

        Returns:
            bool: True if the user is allowed, False otherwise.
        """
        if str(message.from_user.id) in self.config.allowed_user_ids:
            return True
        return False

    def _validate_msg_text_has_code(self, message: telebot.types.Message) -> bool:
        """
        Validates if the message text contains a code number by using a regex search pattern.
        If a match is found, it calls the 'verify_otp_code_in_msg' method and returns the result.
        If no match is found, it logs a message and returns False.

        Parameters:
            self: The instance of the class.
            message (telebot.types.Message): The message object received.

        Returns:
            bool: True if the message text contains a code number, False otherwise.
        """
        bracket1 = "{"
        bracket2 = "}"
        regex_search = r"^\d{0}{1}{2}$".format(bracket1, self.config.otp_length, bracket2)
        self.logger.debug(msg="regex search string")
        match = re.search(regex_search, message.text, re.IGNORECASE)
        if match:
            return self._verify_otp_code_in_msg(message=message)

        self.logger.debug(msg="no code number detected")
        return False

    def _verify_otp_code_in_msg(self, message: telebot.types.Message) -> bool:
        """
        Verifies if the received message text contains a valid TOTP code.
        If the code is valid, it logs a message and returns True.
        If the code is invalid, it logs a message and returns False.

        Parameters:
            self: The instance of the class.
            message (telebot.types.Message): The message object received.

        Returns:
            bool: True if the message text contains a valid TOTP code, False otherwise.
        """
        totp_config = pyotp.TOTP(s=self.config.otp_password, digits=self.config.otp_length,
                                 digest=self.config.hash_type, interval=self.config.otp_interval)
        if totp_config.verify(message.text):
            self.logger.info(msg=message.text + " TOTP code correct")
            self.door_open_task_queue.put(
                Open_Door_Task(open=True, reply=True, chat_id=self.config.telegram_chat_nr, message=message))
            self.bot.reply_to(message=message, text="Code accepted.")
            self.logger.info(msg="Door opened for 5 Sec.")
            return True
        else:
            self.logger.info(msg="wrong totp code received " + message.text)
            self.bot.reply_to(message=message, text="TOTP code is wrong")
            return False
