import telebot
import logging
import threading
import re
from door import opener
from camera import blink_cam, cam_common
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from otp import otp
from config import config_util
from bot import send_msg
logger: logging.Logger = logging.getLogger(name="receive_msg")


class ReceivingMessage:
    """Receiving Telegram Bot messages"""

    telebot.apihelper.RETRY_ON_ERROR = True

    def __init__(self,
                 bot: telebot.TeleBot,
                 config: config_util.Configuration,
                 blink_instance: object,
                 blink_auth_instance: object) -> None:
        """Initial class definition."""
        self.logger: logging.Logger = logging.getLogger(name="ReceivingMessage")
        self.config: config_util.Configuration = config
        self.logger.debug(msg="initialize receive_msg class instance")
        self.bot: telebot.TeleBot = bot
        self.blink: Blink = blink_instance
        self.auth: Auth = blink_auth_instance
        self.blink_json_data: dict[any, any] = {}
        foto_list: list[str] = ["foto", "Foto", "FOTO"]
        blink_list: list[str] = ["blink", "Blink", "BLINK"]
        picam_list: list[str] = ["picam", "Picam", "PICAM", "PiCam"]
        blink_auth_list: list[str] = ["blink_auth", "Blink_auth", "Blink_Auth", "BLINK_AUTH"]
        self.foto_command = self.bot.message_handler(commands=foto_list)(self.take_foto)
        self.blink_command = self.bot.message_handler(commands=blink_list)(self.take_blink_foto)
        self.picam_command = self.bot.message_handler(commands=picam_list)(self.take_picam_foto)
        self.blink_auth_command = self.bot.message_handler(commands=blink_auth_list)(self.register_bink_authentication)
        self.message_request = self.bot.message_handler(func=lambda message: message.content_type == "text")(self.receive_any_msg_text)

    def start(self) -> None:
        self.logger.debug(msg="start bot endless polling")
        self.bot.infinity_polling(logger_level=logging.DEBUG, timeout=10, long_polling_timeout=5)

    def receive_any_msg_text(self, message: telebot.types.Message) -> None:
        # check if received from allowed telegram chat group and allowed
        # user id has send.
        if self.get_allowed(message=message):
            # check is message text has TOTP code and if correct open door, otherwise do nothing
            self.validate_msg_text_has_code(message=message)

    def take_foto(self, message: telebot.types.Message) -> None:
        
        logger.debug(f"received /foto request with message {message}")
        
        # check if received from allowed telegram chat group and
        # if it was send from allowed user id.
        if self.get_allowed(message=message):
            # start new thread for taking a foto
            rcv_foto_thread = threading.Thread(
                target=self.rcv_foto, args=(message,)
            )
            rcv_foto_thread.start()
            rcv_foto_thread.join()

    def rcv_foto(self, message: telebot.types.Message) -> bool:
        """
        Received request to take a foto.

        :return: bool
        :rtype: bool
        """
        logger.debug(msg="Foto request received")
        result: bool = send_msg.telegram_send_message(
            bot=self.bot, telegram_chat_nr=self.config.telegram_chat_nr, message="I will send a foto!"
        )

        cam_common.choose_camera(auth=self.auth, blink=self.blink, config_class_instance=self.config)
        return bool(result)

    def take_picam_foto(self, message: telebot.types.Message) -> None:

        logger.debug(f"received /picam request with message {message}")

        # check if received from allowed telegram chat group and
        # if it was send from allowed user id.
        if self.get_allowed(message=message):
            # start new thread for taking a foto
            rcv_foto_thread = threading.Thread(
                target=self.rcv_picam_foto, args=(message,)
            )
            rcv_foto_thread.start()
            rcv_foto_thread.join()

    def rcv_picam_foto(self, message: telebot.types.Message) -> bool:
        """
        take picam switch case condition detect from received message

        :return: boolean
        :rtype: bool
        """
        self.logger.debug(msg="text match PiCam foto found")
        return cam_common.picam_take_photo(auth=self.auth,
                                           blink=self.blink,
                                           config_class_instance=self.config)

    def take_blink_foto(self, message: telebot.types.Message) -> None:

        logger.debug(f"received /blink request with message {message}")

        # check if received from allowed telegram chat group and
        # if it was send from allowed user id.
        if self.get_allowed(message=message):
            # start new thread for taking a foto
            blink_foto_thread = threading.Thread(
                target=self.rcv_blink_foto, args=(message,)
            )
            blink_foto_thread.start()
            blink_foto_thread.join()

    def rcv_blink_foto(self, message: telebot.types.Message) -> bool:
        """
        take blinkcam switch case condition detect from received message

        :return: boolean
        :rtype: bool
        """
        self.logger.debug(msg="text match blink cam foto found")
        return cam_common.blink_take_photo(auth=self.auth,
                                           blink=self.blink,
                                           config_class_instance=self.config)

    def register_bink_authentication(self, message: telebot.types.Message) -> None:

        logger.debug(f"received /blink_auth request with message {message}")

        # check if received from allowed telegram chat group and
        # if it was send from allowed user id.
        if self.get_allowed(message=message):
            # start new thread for taking a foto
            blink_auth_thread = threading.Thread(
                target=self.rcv_blink_auth, args=(message,)
            )
            blink_auth_thread.start()
            blink_auth_thread.join()

    def rcv_blink_auth(self, message: telebot.types.Message) -> bool:
        """
        received request to add blink cam 2FA authentication code

        :return: success status
        :rtype: boolean
        """
        match = re.search(r"(?<=^blink.)\d{6}", message.text, re.IGNORECASE)
        if match:
            self.logger.info(msg="blink token received - will save config")
            send_msg.telegram_send_message(
                bot=self.bot,
                telegram_chat_nr=self.config.telegram_chat_nr,
                message="Blink token received " + match.group(0),
            )
            blink_cam.add_2fa_blink_token(
                token=match.group(0), blink=self.blink, auth=self.auth
            )
            blink_cam.blink_compare_config(auth=self.auth,
                                           blink=self.blink,
                                           config_class_instance=self)
            return True

        self.logger.debug(msg="no blink token detected")
        return False

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
        if otp.verify_totp_code(
            to_verify=message.text,
            my_secret=self.config.otp_password,
            length=self.config.otp_length,
            interval=self.config.otp_interval,
            hash_type=self.config.hash_type,
        ):
            
            self.logger.info(msg=message.text + " TOTP code correct")
            self.bot.reply_to(message=message, text="Code accepted.")

            opener.open_door(door_opener_port=self.config.door_summer, run_on_raspberry=self.config.run_on_raspberry)
            
            self.logger.info(msg="Door opened for 5 Sec.")
            return True
        else:
            self.logger.info(msg="wrong totp code received " + message.text)
            self.bot.reply_to(message=message, text="TOTP code is wrong")
            return False
