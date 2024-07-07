from __future__ import annotations

import asyncio
import logging
import queue
import re
import pyotp
import telebot


from config import config_util
from config.data_class import Camera_Task, Open_Door_Task

logger: logging.Logger = logging.getLogger(name="receive_msg")


class ReceivingMessage():
    """Receiving Telegram Bot messages"""

    telebot.apihelper.RETRY_ON_ERROR = True

    def __init__(self,
                 bot: telebot.TeleBot,
                 config: config_util.Configuration,
                 loop,
                 camera_task_queue_async: asyncio.Queue,
                 door_open_task_queue: queue.Queue
                 ) -> None:
        """Initial class definition."""
        self.logger: logging.Logger = logging.getLogger(name="ReceivingMessage")
        self.config: config_util.Configuration = config
        self.loop = loop
        self.camera_task_queue_async: asyncio.Queue = camera_task_queue_async
        self.door_open_task_queue = door_open_task_queue
        self.logger.debug(msg="initialize receive_msg class instance")
        self.bot: telebot.TeleBot = bot
        foto_list: list[str] = ["foto", "Foto", "FOTO"]
        blink_list: list[str] = ["blink", "Blink", "BLINK"]
        picam_list: list[str] = ["picam", "Picam", "PICAM", "PiCam"]
        blink_auth_list: list[str] = ["blink_auth", "Blink_auth", "Blink_Auth", "BLINK_AUTH"]
        self.foto_command = self.bot.message_handler(commands=foto_list)(self.take_foto)
        self.blink_command = self.bot.message_handler(commands=blink_list)(self.take_blink_foto)
        self.picam_command = self.bot.message_handler(commands=picam_list)(self.take_picam_foto)
        self.blink_auth_command = self.bot.message_handler(commands=blink_auth_list)(self.register_bink_authentication)
        self.message_request = self.bot.message_handler(func=lambda message: message.content_type == "text")(
            self.receive_any_msg_text)

    def start(self) -> None:

        self.logger.debug(msg="start bot endless polling")
        try:
            self.bot.infinity_polling(logger_level=logging.DEBUG, timeout=10, long_polling_timeout=5)
        except Exception as err:
            self.logger.error("Error: {0}".format(err))
            pass

    def stop(self):
        self.bot.stop_polling()
        self.bot.remove_webhook()
        # self.bot_thread.join()

    def signal_handler(self, sig, frame):
        self.logger.info("Signal received, stopping the bot...")
        self.stop()
        self.logger.info("Bot stopped gracefully.")

    def receive_any_msg_text(self, message: telebot.types.Message) -> None:
        # check if received from allowed telegram chat group and allowed
        # user id has send.
        if self.get_allowed(message=message):
            # check is message text has TOTP code and if correct open door, otherwise do nothing
            self.validate_msg_text_has_code(message=message)

    def take_foto(self, message: telebot.types.Message) -> None:

        logger.debug(f"received foto request with message {message}")

        # check if received from allowed telegram chat group and
        # if it was send from allowed user id.
        if self.get_allowed(message=message):
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply=True,
                    photo=True
                )
            ),
                self.loop)

    def take_picam_foto(self, message: telebot.types.Message) -> None:

        logger.debug(f"received /picam request with message {message}")

        # check if received from allowed telegram chat group and
        # if it was send from allowed user id.
        if self.get_allowed(message=message):
            # start new thread for taking a foto
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply=True,
                    picam_photo=True
                )
            ),
                self.loop)

    def take_blink_foto(self, message: telebot.types.Message) -> None:

        logger.debug(f"received blink request with message {message}")

        # check if received from allowed telegram chat group and
        # if it was send from allowed user id.
        if self.get_allowed(message=message):
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reply=True,
                    blink_photo=True
                )
            ),
                self.loop)

    def register_bink_authentication(self, message: telebot.types.Message) -> None:

        logger.debug(f"received /blink_auth request with message {message}")

        # check if received from allowed telegram chat group and
        # if it was send from allowed user id.
        if self.get_allowed(message=message):
            # start new thread for taking a foto
            self.rcv_blink_auth(message)

    def rcv_blink_auth(self, message: telebot.types.Message) -> None:
        """
        received request to add blink cam 2FA authentication code

        :return: success status
        :rtype: boolean
        """
        match = re.search(r"(?<=^blink.)\d{6}", message.text, re.IGNORECASE)
        if match:
            self.logger.info(msg="blink token received - will save config")
            message = "Blink token received " + match.group(0)
            self.bot.reply_to(message=message, text=message)
            asyncio.set_event_loop(self.loop)
            asyncio.run_coroutine_threadsafe(self.camera_task_queue_async.put(
                Camera_Task(
                    blink_mfa=match.group(0),
                    chat_id=message.chat.message_id,
                    message_id=message.message_id,
                    reply=True
                )
            ),
                self.loop)
            return

        self.logger.debug(msg="no blink token detected")
        message = "Blink token received " + match.group(0)
        self.bot.reply_to(message=message, text="no blink token detected")
        return

    def get_allowed(self, message: telebot.types.Message) -> bool:
        """Checks given telegram chat id is allowed id from config
        and perform further check get_allowed_user

        :param message: received telegram message
        :type message: telebot.types.Message
        :return: check result as boolean
        :rtype: bool
        """
        if str(message.chat.id) == self.config.telegram_chat_nr:
            return self.get_allowed_user(message=message)
        return False

    def get_allowed_user(self, message: telebot.types.Message) -> bool:
        """Checks if given telegram from user id is allowed from config file

        :param message: received telegram message
        :type message: telebot.types.Message
        :return: check result as boolean
        :rtype: bool
        """
        if str(message.from_user.id) in self.config.allowed_user_ids:
            return True
        return False

    def validate_msg_text_has_code(self, message: telebot.types.Message) -> bool:
        """
        Check received message has a code to open door

        :return: success status
        :rtype: boolean
        """
        bracket1 = "{"
        bracket2 = "}"
        regex_search = r"^\d{0}{1}{2}$".format(bracket1, self.config.otp_length,
                                               bracket2)
        self.logger.debug(msg="regex search string")
        match = re.search(regex_search, message.text, re.IGNORECASE)
        if match:
            return self.verify_otp_code_in_msg(message=message)

        self.logger.debug(msg="no code number detected")
        return False

    def verify_otp_code_in_msg(self, message: telebot.types.Message) -> bool:
        """
        Verify msg text code if it matches totp code
        and opens the door.

        :return: success status
        :rtype: boolean
        """

        totp_config = pyotp.TOTP(s=self.config.otp_password,
                                 digits=self.config.otp_length,
                                 digest=self.config.hash_type,
                                 interval=self.config.otp_interval)
        if totp_config.verify(message.text):
            self.logger.info(msg=message.text + " TOTP code correct")
            self.door_open_task_queue.put(Open_Door_Task(open=True, reply=True, chat_id=self.config.telegram_chat_nr, message_id=message.id))
            self.bot.reply_to(message=message, text="Code accepted.")
            self.logger.info(msg="Door opened for 5 Sec.")
            return True
        else:
            self.logger.info(msg="wrong totp code received " + message.text)
            self.bot.reply_to(message=message, text="TOTP code is wrong")
            return False
