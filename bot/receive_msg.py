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
        enable_list: list[str] = ["enable", "Enable", "ENABLE"]
        disable_list: list[str] = ["disable", "Disable", "DISABLE"]
        web_enable_list: list[str] = ["web_enable", "Web_enable", "WEB_ENABLE"]
        web_disable_list: list[str] = ["web_disable", "Web_disable", "WEB_DISABLE"]
        list_user_list: list[str] = ["list_user", "List_user", "List_User", "LIST_USER"]
        list_web_user_list: list[str] = ["list_web_user", "List_web_user", "List_Web_User", "LIST_WEB_USER"]
        camera_get_list: list[str] = ["camera_get", "Camera_get", "CAMERA_GET"]
        camera_switch_list: list[str] = ["camera_switch", "Camera_switch", "CAMERA_SWITCH"]
        camera_set_list: list[str] = ["camera_set", "Camera_set", "CAMERA_SET"]
        help_list: list[str] = ["help", "Help", "HELP"]
        self.foto_command = self.bot.message_handler(commands=foto_list)(self.take_foto)
        self.blink_command = self.bot.message_handler(commands=blink_list)(self.take_blink_foto)
        self.picam_command = self.bot.message_handler(commands=picam_list)(self.take_picam_foto)
        self.blink_auth_command = self.bot.message_handler(commands=blink_auth_list)(self.register_bink_authentication)
        self.enable_command = self.bot.message_handler(commands=enable_list)(self.enable_user)
        self.disable_command = self.bot.message_handler(commands=disable_list)(self.disable_user)
        self.web_enable_command = self.bot.message_handler(commands=web_enable_list)(self.enable_web_user)
        self.web_disable_command = self.bot.message_handler(commands=web_disable_list)(self.disable_web_user)
        self.list_user_command = self.bot.message_handler(commands=list_user_list)(self.list_user)
        self.list_web_user_command = self.bot.message_handler(commands=list_web_user_list)(self.list_web_user)
        self.camera_get_command = self.bot.message_handler(commands=camera_get_list)(self.get_camera_config)
        self.camera_switch_command = self.bot.message_handler(commands=camera_switch_list)(self.switch_camera)
        self.camera_set_command = self.bot.message_handler(commands=camera_set_list)(self.set_camera_config)
        self.help_command = self.bot.message_handler(commands=help_list)(self.send_help)
        self.message_request = self.bot.message_handler(func=lambda message: message.content_type == "text")(
            self.receive_any_msg_text)

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

    def receive_any_msg_text(self, message: telebot.types.Message) -> None:
        """
        Check if the message is received from an allowed telegram chat group and allowed user ID.
        If the conditions are met, check if the message text has a TOTP code and open the door if correct, otherwise do nothing.

        Parameters:
            message (telebot.types.Message): The message object received.

        Returns:
            None
        """
        if self.__get_allowed(message=message):
            # check is message text has TOTP code and if correct open door, otherwise do nothing
            self.__validate_msg_text_has_code(message=message)

    def take_foto(self, message: telebot.types.Message) -> None:
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
        self.__log_command_received(message)
        if self.__get_allowed(message=message):
            self.__schedule_camera_task(
                Camera_Task(chat_id=message.chat.id, message=message, reply=True, photo=True)
            )

    def take_picam_foto(self, message: telebot.types.Message) -> None:
        """
        Takes a photo request specific to the PiCam (foto API [PiCamAPI](https://github.com/OliverDrechsler/PiCam_API)) from a telegram message and puts it into a camera task queue.

        Args:
            message (telebot.types.Message): The telegram message object containing the photo request.

        Returns:
            None
        """
        self.__log_command_received(message)
        if self.__get_allowed(message=message):
            self.__schedule_camera_task(
                Camera_Task(chat_id=message.chat.id, message=message, reply=True, picam_photo=True)
            )

    def take_blink_foto(self, message: telebot.types.Message) -> None:
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
        self.__log_command_received(message)
        if self.__get_allowed(message=message):
            self.__schedule_camera_task(
                Camera_Task(chat_id=message.chat.id, message=message, reply=True, blink_photo=True)
            )

    def register_bink_authentication(self, message: telebot.types.Message) -> None:
        """
        Registers a Blink authentication based on the received message.

        Args:
            self: the object instance
            message (telebot.types.Message): the message received

        Returns:
            None
        """
        self.__log_command_received(message)
        if self.__get_allowed(message=message):
            # start new thread for taking a foto
            self.__rcv_blink_auth(message)

    def enable_user(self, message: telebot.types.Message) -> None:
        """Enable a configured telegram user via /enable <username>."""
        self.__log_command_received(message)
        self.__set_user_state(message=message, enabled=True)

    def disable_user(self, message: telebot.types.Message) -> None:
        """Disable a configured telegram user via /disable <username>."""
        self.__log_command_received(message)
        self.__set_user_state(message=message, enabled=False)

    def list_user(self, message: telebot.types.Message) -> None:
        """Send enabled/disabled configured telegram users."""
        self.__log_command_received(message)
        if not self.__get_allowed(message=message):
            return

        telegram_state = self.config.get_telegram_user_state()
        web_state = self.config.get_web_user_state()

        def format_state(title: str, state: dict[str, list[str]]) -> str:
            enabled_users = state.get("enabled", [])
            disabled_users = state.get("disabled", [])
            enabled_text = "\n".join([f"- {username}" for username in enabled_users]) or "- none"
            disabled_text = "\n".join([f"- {username}" for username in disabled_users]) or "- none"
            return f"{title}:\nEnabled users:\n{enabled_text}\n\nDisabled users:\n{disabled_text}"

        message_text = (
            f"{format_state('Telegram users', telegram_state)}\n\n"
            f"{format_state('Web users', web_state)}"
        )
        self.bot.reply_to(message=message, text=message_text)

    def enable_web_user(self, message: telebot.types.Message) -> None:
        """Enable a configured flask web user via /web_enable <username>."""
        self.__log_command_received(message)
        self.__set_web_user_state(message=message, enabled=True)

    def disable_web_user(self, message: telebot.types.Message) -> None:
        """Disable a configured flask web user via /web_disable <username>."""
        self.__log_command_received(message)
        self.__set_web_user_state(message=message, enabled=False)

    def list_web_user(self, message: telebot.types.Message) -> None:
        """Send enabled/disabled configured flask web users."""
        self.__log_command_received(message)
        if not self.__get_allowed(message=message):
            return

        state = self.config.get_web_user_state()
        enabled_users = state.get("enabled", [])
        disabled_users = state.get("disabled", [])

        enabled_text = "\n".join([f"- {username}" for username in enabled_users]) or "- none"
        disabled_text = "\n".join([f"- {username}" for username in disabled_users]) or "- none"
        message_text = f"Enabled web users:\n{enabled_text}\n\nDisabled web users:\n{disabled_text}"
        self.bot.reply_to(message=message, text=message_text)

    def send_help(self, message: telebot.types.Message) -> None:
        """Send list of available bot commands."""
        self.__log_command_received(message)
        if not self.__get_allowed(message=message):
            return

        help_text = (
            "Available commands:\n"
            "\n"
            "<send only code to open>\n"
            "\n"
            "/foto   # take from default camera a foto\n"
            "/blink  # takes a blink camera foto\n"
            "/picam. # takes a picam camera foto\n"
            "/blink_auth <token>  # authenticates required blink 2FA again with given code\n"
            "/enable <username>\n"
            "/disable <username>\n"
            "/list_user\n"
            "/web_enable <username>\n"
            "/web_disable <username>\n"
            "/list_web_user\n"
            "/camera_get  # shows camera config\n"
            "/camera_switch  # switches active camera between blink and picam\n"
            "/camera_set <section> <option> <on|off>  # changes camera config option\n"
            "/help  # this help\n"
        )
        self.bot.send_message(chat_id=message.chat.id, text=help_text)

    def get_camera_config(self, message: telebot.types.Message) -> None:
        """Send current camera configuration state."""
        self.__log_command_received(message)
        if not self.__get_allowed(message=message):
            return

        state = self.config.get_camera_config_state()
        message_text = (
            "Camera config:\n"
            f"photo_general.default_camera_type: {state['photo_general']['default_camera_type']}\n"
            f"photo_general.enable_detect_daylight: {state['photo_general']['enable_detect_daylight']}\n"
            f"blink.enabled: {state['blink']['enabled']}\n"
            f"blink.night_vision: {state['blink']['night_vision']}\n"
            f"blink.image_brightening: {state['blink']['image_brightening']}\n"
            f"picam.enabled: {state['picam']['enabled']}\n"
            f"picam.night_vision: {state['picam']['night_vision']}\n"
            f"picam.image_brightening: {state['picam']['image_brightening']}"
        )
        self.bot.reply_to(message=message, text=message_text)

    def switch_camera(self, message: telebot.types.Message) -> None:
        """Switch default camera type between blink and picam."""
        self.__log_command_received(message)
        if not self.__is_admin(message=message):
            return

        try:
            new_type = self.config.switch_default_camera_type()
        except Exception as err:
            self.logger.error("switch camera failed: %s", err)
            self.bot.reply_to(message=message, text="Failed to switch camera")
            return

        self.bot.reply_to(message=message, text=f"default_camera_type switched to {new_type}")

    def set_camera_config(self, message: telebot.types.Message) -> None:
        """Set mutable camera config options via /camera_set <section> <option> <on|off>."""
        self.__log_command_received(message)
        if not self.__is_admin(message=message):
            return

        match = re.search(
            r"^/camera_set\s+([A-Za-z_]+)\s+([A-Za-z_]+)\s+(on|off|true|false|1|0)$",
            message.text or "",
            re.IGNORECASE,
        )
        if not match:
            self.bot.reply_to(message=message, text="Usage: /camera_set <section> <option> <on|off>")
            return

        section = match.group(1).lower()
        option = match.group(2).lower()
        value_raw = match.group(3).lower()
        bool_value = value_raw in ("on", "true", "1")

        if section == "photo_general" and option == "default_camera_type":
            self.bot.reply_to(message=message, text="Use /camera_switch for default_camera_type")
            return

        try:
            self.config.set_camera_bool_option(section=section, option=option, value=bool_value)
        except ValueError:
            self.bot.reply_to(message=message, text=f"Unsupported option {section}.{option}")
            return
        except Exception as err:
            self.logger.error("camera_set failed: %s", err)
            self.bot.reply_to(message=message, text="Failed to write config")
            return

        self.bot.reply_to(message=message, text=f"{section}.{option} set to {bool_value}")

    def __rcv_blink_auth(self, message: telebot.types.Message) -> None:
        self.logger.debug(f"received blink token with message {message}")
        match = re.search(r'^/blink_auth (\d{6})$', message.text, re.IGNORECASE)
        if match:
            self.logger.info(msg="blink token received - will save config")
            message_text = "Blink token received " + match.group(1)
            self.bot.reply_to(message=message, text=message_text)
            self.__schedule_camera_task(
                Camera_Task(blink_mfa=match.group(1), chat_id=message.chat.id, message=message, reply=True)
            )
            return

        self.logger.debug(msg="no blink token detected")
        self.bot.reply_to(message=message, text="no blink token detected")
        return

    def __schedule_camera_task(self, task: Camera_Task) -> None:
        coroutine = self.camera_task_queue_async.put(task)
        try:
            future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        except Exception as err:
            coroutine.close()
            self.logger.error("Error scheduling camera task: %s", err)
            return
        future.add_done_callback(self.__log_camera_task_failure)

    def __log_command_received(self, message: telebot.types.Message) -> None:
        """Log a Telegram command, its value, and sender without exposing secrets."""
        command_text = message.text if isinstance(message.text, str) else ""
        command, separator, value = command_text.partition(" ")
        command = command or "<unknown>"
        value = value if separator else "<none>"
        if command.casefold() == "/blink_auth":
            value = "<redacted>"
        from_user = getattr(message, "from_user", None)
        username = getattr(from_user, "username", None) or "<no username>"
        user_id = getattr(from_user, "id", "<unknown>")
        self.logger.info(
            "Received Telegram command %s with value %s from user %s (id=%s)",
            command,
            value,
            username,
            user_id,
        )

    def __log_camera_task_failure(self, future) -> None:
        try:
            future.result()
        except Exception as err:
            self.logger.error("Error scheduling camera task: %s", err)

    def __set_user_state(self, message: telebot.types.Message, enabled: bool) -> None:
        """
        Update enabled/disabled status for a configured telegram username.
        Only configured admins in the configured chat may use this command.
        """
        self.logger.debug("__set_user_state")
        if not self.__is_admin(message=message):
            self.logger.debug("__set_user_state not admin")
            return

        match = re.search(r"^/(enable|disable)\s+([A-Za-z0-9_]+)$", message.text or "", re.IGNORECASE)
        if not match:
            self.logger.debug("__set_user_state not regex match")
            command = "enable" if enabled else "disable"
            self.bot.reply_to(message=message, text=f"Usage: /{command} <username>")
            return

        username = match.group(2)
        allowed_lookup = {
            str(allowed_username).lower(): str(allowed_username)
            for allowed_username in self.config.allowed_user_ids
        }
        username_key = allowed_lookup.get(str(username).lower())
        if not username_key:
            self.logger.debug("__set_user_state user not in allowed")
            return

        state = self.config.get_telegram_user_state()
        enabled_users = [user for user in state["enabled"] if user != username_key]
        disabled_users = [user for user in state["disabled"] if user != username_key]

        if enabled:
            enabled_users.append(username_key)
        else:
            admin_usernames = {str(admin_user).casefold() for admin_user in self.config.admin_users}
            if username_key.casefold() in admin_usernames:
                self.bot.reply_to(message=message, text=f"{username_key} is admin and cannot be disabled")
                return
            disabled_users.append(username_key)

        new_state = {"enabled": enabled_users, "disabled": disabled_users}
        self.config.write_telegram_user_state(new_state)
        self.bot.reply_to(message=message, text=f"{username_key} {'enabled' if enabled else 'disabled'}")

    def __is_admin(self, message: telebot.types.Message) -> bool:
        """Return True when the telegram user may manage enable/disable commands."""
        if str(message.chat.id) != str(self.config.telegram_chat_nr):
            return False
        username = self.__get_username_for_user_id(message=message)
        admin_users = [str(admin_user) for admin_user in self.config.admin_users]
        self.logger.debug(f"__is_admin {username} in {admin_users}")
        return username in admin_users

    def __set_web_user_state(self, message: telebot.types.Message, enabled: bool) -> None:
        """
        Update enabled/disabled status for a configured flask web username.
        Only configured admins in the configured telegram chat may use this command.
        """
        if not self.__is_admin(message=message):
            return

        command = "web_enable" if enabled else "web_disable"
        match = re.search(r"^/(web_enable|web_disable)\s+([A-Za-z0-9_]+)$", message.text or "", re.IGNORECASE)
        if not match:
            self.bot.reply_to(message=message, text=f"Usage: /{command} <username>")
            return

        username = match.group(2)
        allowed_lookup = {
            str(allowed_username).lower(): str(allowed_username)
            for allowed_username in self.config.web_user_dict.keys()
        }
        username_key = allowed_lookup.get(str(username).lower())
        if not username_key:
            self.bot.reply_to(message=message, text=f"Unknown web user: {username}")
            return

        state = self.config.get_web_user_state()
        enabled_users = [user for user in state["enabled"] if user != username_key]
        disabled_users = [user for user in state["disabled"] if user != username_key]

        if enabled:
            enabled_users.append(username_key)
        else:
            admin_usernames = {str(admin_user).casefold() for admin_user in self.config.admin_users}
            if username_key.casefold() in admin_usernames:
                self.bot.reply_to(message=message, text=f"{username_key} is admin and cannot be disabled")
                return
            disabled_users.append(username_key)

        new_state = {"enabled": enabled_users, "disabled": disabled_users}
        self.config.write_web_user_state(new_state)
        self.bot.reply_to(message=message, text=f"web user {username_key} {'enabled' if enabled else 'disabled'}")

    def __get_allowed(self, message: telebot.types.Message) -> bool:
        """
        Checks if the message chat ID matches the configured Telegram chat number and calls get_allowed_user
        if the condition is met. Returns True if the user is allowed, False otherwise.

        Parameters:
            message (telebot.types.Message): The message object received.

        Returns:
            bool: True if the user is allowed, False otherwise.
        """
        if str(message.chat.id) == str(self.config.telegram_chat_nr):
            return self.__get_allowed_user(message=message)
        return False

    def __get_allowed_user(self, message: telebot.types.Message) -> bool:
        """
        Checks if the message from_user ID matches the configured allowed user IDs.

        Parameters:
            message (telebot.types.Message): The message object received.

        Returns:
            bool: True if the user is allowed, False otherwise.
        """
        username = self.__get_username_for_user_id(message=message)
        if username is None:
            return False

        state = self.config.get_telegram_user_state()
        if username in state.get("disabled", []):
            return False
        if username in state.get("enabled", []):
            return True
        return False

    def __get_username_for_user_id(self, message: telebot.types.Message) -> str | None:
        """Return configured username for the telegram user id in the message."""
        message_user_id = str(message.from_user.id)
        for username, user_id in self.config.allowed_user_ids.items():
            if str(user_id) == message_user_id:
                return username
        return None

    def __get_message_username(self, message: telebot.types.Message) -> str:
        """Return telegram username without leading @."""
        username = getattr(message.from_user, "username", "") or ""
        self.logger.debug(f"__get_message_username {username}")
        return username.removeprefix("@")

    def __validate_msg_text_has_code(self, message: telebot.types.Message) -> bool:
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
            return self.__verify_otp_code_in_msg(message=message)

        self.logger.debug(msg="no code number detected")
        return False

    def __verify_otp_code_in_msg(self, message: telebot.types.Message) -> bool:
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
            self.bot.send_message(chat_id=message.chat.id, text="Code accepted.")
            self.logger.info(msg="Door opened for 5 Sec.")
            return True
        else:
            self.logger.info(msg="wrong totp code received " + message.text)
            self.bot.send_message(chat_id=message.chat.id, text="TOTP code is wrong")
            return False
