import telebot
import logging
# import time
import os

logger: logging.Logger = logging.getLogger(name="send_telegram_msg")


def telegram_send_message(bot: telebot.TeleBot, telegram_chat_nr: str, message: str) -> bool:
    """
    Send a telegram message to chat group with number

    :param bot: telegram bot class instance
    :type bot: object
    :param telegram_chat_nr: telegram chat group number
    :type telegram_chat_nr: str
    :param message: Message text
    :type message: str
    :return: Success or failsure
    :rtype: bool
    """
    result: telebot.types.Message = bot.send_message(telegram_chat_nr, message)
    logger.info("send message : " + message)
    if result is None:
        return False
    else:
        return True


def telegram_send_photo(
    bot: telebot.TeleBot, telegram_chat_nr: str, common_image_path: str,
) -> bool:
    """
     Send a telegram photo to chat group with number

    :param bot: telegram bot class instance
    :type bot: object
    :param telegram_chat_nr: telegram chat group number
    :type telegram_chat_nr: str
    :param common_image_path: local path where to store the image
    :type common_image_path: str
    :return: Success or failsure
    :rtype: bool
    """
    result: telebot.types.Message = bot.send_photo(telegram_chat_nr, photo=open(common_image_path, "rb"))
    logger.info(msg="send a foto: success")
    if os.path.exists(path=common_image_path):
        os.remove(path=common_image_path)
    if result is None:
        return False
    else:
        return True
    
    

