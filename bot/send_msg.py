import logging
import queue
import threading

import telebot

from config import config_util
from config.data_class import Message_Task

logger: logging.Logger = logging.getLogger(name="send_telegram_msg")


class SendMessage():
    telebot.apihelper.RETRY_ON_ERROR = True

    def __init__(self, shutdown_event: threading.Event, config: config_util.Configuration, loop,
                 message_task_queue: queue.Queue) -> None:
        """
        Initializes the SendMessage class.

        Args:
            shutdown_event (threading.Event): The event used to stop the polling of the bot.
            config (config_util.Configuration): The configuration object.
            loop: The event loop.
            message_task_queue (queue.Queue): The queue containing the message tasks.

        Returns:
            None
        """
        self.logger: logging.Logger = logging.getLogger(name="SendMessage")
        self.config: config_util.Configuration = config
        self.loop = loop
        self.message_task_queue = message_task_queue
        self.logger.debug(msg="initialize send_msg class instance")
        self.bot: telebot.TeleBot = self.config.bot
        self.stop_polling = shutdown_event
        self.bot.__stop_polling = shutdown_event

    def start(self) -> None:
        """
        Starts the thread endless loop to send telegram bot messages.

        This function runs in an infinite loop until the `stop_polling` event is set. It continuously retrieves tasks from the `message_task_queue` and processes them. If a task is an instance of `Message_Task`, it performs the following actions based on the task attributes:
        - If `task.send` is True, it sends a message to the specified chat using the `send_message` method.
        - If `task.reply` is True, it replies to the specified message with the given text using the `reply_message` method.
        - If `task.photo` is True, it sends a photo to the specified chat using the `send_photo` method.

        If an exception occurs during the execution of the loop, it logs the error and continues.

        After the loop finishes, it calls the `stop` method.

        Parameters:
            self (SendMessage): The instance of the `SendMessage` class.

        Returns:
            None
        """
        self.logger.debug(msg="thread endless loop send telegram bot messages")

        while not self.stop_polling.is_set():
            try:
                task = self.message_task_queue.get()
                if task is None:  # Exit signal
                    break
                logging.info(f"received task: {task}")
                if isinstance(task, Message_Task):
                    if (task.send):
                        self._send_message(chat_id=task.chat_id, text=task.data_text)
                    if (task.reply):
                        self._reply_message(chat_id=task.chat_id, message=task.message, text=task.data_text)
                    if (task.photo):
                        self._send_photo(chat_id=task.chat_id, image_path=task.filename)
            except Exception as err:
                self.logger.error("Error: {0}".format(err))
                pass
        self.stop()

    def stop(self) -> None:
        """
        A method to stop the bot. It logs the action of stopping bot polling, stops the bot from polling, removes the webhook.
        """
        self.logger.info(msg="stop bot stop polling")
        self.bot.stop_polling()
        self.logger.info(msg="stop bot remove webhook")
        self.bot.remove_webhook()

    def _reply_message(self, chat_id: str, text: str, message: telebot.types.Message):
        """
        Reply to a message in a chat.

        Args:
            chat_id (str): The ID of the chat.
            text (str): The text of the reply message.
            message (telebot.types.Message): The message to reply to.

        Returns:
            None

        This function sends a reply message to a chat using the Telegram Bot API. It uses the `reply_to` method of the `bot` object to send the reply. The reply message contains the provided `text`. The function logs the reply message using the `logger` object.
        """
        self.bot.reply_to(message=message, text=text)
        self.logger.info("reply message : " + text)

    def _send_message(self, chat_id: str, text: str) -> None:
        """
        Send a message to a specified chat using the Telegram Bot API.

        Args:
            chat_id (str): The ID of the chat.
            text (str): The text of the message to be sent.

        Returns:
            None
        """
        self.bot.send_message(chat_id=chat_id, text=text)
        self.logger.info("send message : " + text)

    def _send_photo(self, chat_id: str, image_path: str) -> None:
        """
        Send a photo to a specified chat using the Telegram Bot API.

        Args:
            chat_id (str): The ID of the chat.
            image_path (str): The path to the image file to be sent.

        Returns:
            None
        """
        self.bot.send_photo(chat_id=chat_id, photo=open(file=image_path, mode="rb"))
        self.logger.info(msg="send a foto: success")
