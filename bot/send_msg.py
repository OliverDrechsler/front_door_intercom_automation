import logging
import os
import queue

import telebot

from config import config_util
from config.data_class import Message_Task

logger: logging.Logger = logging.getLogger(name="send_telegram_msg")


class SendMessage():
    telebot.apihelper.RETRY_ON_ERROR = True

    def __init__(self,
                 bot: telebot.TeleBot,
                 config: config_util.Configuration,
                 loop,
                 message_task_queue: queue.Queue
                 ) -> None:
        """Initial class definition."""
        self.logger: logging.Logger = logging.getLogger(name="SendMessage")
        self.config: config_util.Configuration = config
        self.loop = loop
        self.message_task_queue = message_task_queue
        self.logger.debug(msg="initialize send_msg class instance")
        self.bot: telebot.TeleBot = bot

    def start(self) -> None:
        logger.debug(msg="thread endless loop send telegram bot messages")
        try:
            while True:
                task = self.message_task_queue.get()
                if task is None:  # Exit signal
                    break
                logging.info(f"received task: {task}")
                if isinstance(task, Message_Task):
                    if (task.send):
                        self.send_message(chat_id=task.chat_id, text=task.data_text)
                    if (task.reply):
                        self.reply_message(chat_id=task.chat_id, message=task.message, text=task.data_text)
                    if (task.photo):
                        self.send_photo(chat_id=task.chat_id, image_path=task.filename)
        except Exception as err:
            self.logger.error("Error: {0}".format(err))
            pass

#
# ToDo rework  The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.
#
    def reply_message(self, chat_id: str, text: str, message: telebot.types.Message):
        self.bot.reply_to(message=message, text=text)
        logger.info("reply message : " + text)

    def send_message(self, chat_id: str, text: str) -> None:
        self.bot.send_message(chat_id=chat_id, text=text)
        logger.info("send message : " + text)

    def send_photo(self, chat_id: str, image_path: str) -> None:
        """
         Send a telegram photo to chat group with number
        """
        self.bot.send_photo(chat_id=chat_id, photo=open(file=image_path, mode="rb"))
        logger.info(msg="send a foto: success")
