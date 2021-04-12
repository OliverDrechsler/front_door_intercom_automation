from __future__ import annotations
import telepot
import urllib3
import logging
import time
import os

logger = logging.getLogger('send_telegram_msg')


def telegram_send_message(bot: object, telegram_chat_nr: str, message: str) -> bool:
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
    # bot = telepot.Bot(self.token)
    bot.getMe()
    try:
        telepot.api._onetime_pool_spec = (
            urllib3.PoolManager,
            dict(num_pools=1, maxsize=1, retries=60, timeout=1))
        result = bot.sendMessage(telegram_chat_nr, message)
        logger.info("send message : " + message)
        return bool(result)

    except:
        time.sleep(5)
        try:
            telepot.api._onetime_pool_spec = (
                urllib3.PoolManager,
                dict(num_pools=1, maxsize=1, retries=9, timeout=30))
            result = bot.sendMessage(telegram_chat_nr, message)
            logger.info("send message second try : " + message)
            return bool(result)

        except:
            return False

        return False


def telegram_send_photo(bot: object, telegram_chat_nr: str, common_image_path: str,) -> bool:
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
    # bot = telepot.Bot(token)
    bot.getMe()
    try:
        telepot.api._onetime_pool_spec = (
            urllib3.PoolManager,
            dict(num_pools=1, maxsize=1, retries=60, timeout=1))
        result = bot.sendPhoto(telegram_chat_nr, photo=open(common_image_path, 'rb'))
        logger.info("send a foto: success")
        if os.path.exists(common_image_path):
            os.remove(common_image_path)
        return bool(result)
        
    except:
        logger.info("send a foto: Error occured")
        if os.path.exists(common_image_path):
            os.remove(common_image_path)
        return False
