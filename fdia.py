#!/usr/bin/env python3
from __future__ import annotations
from common import config_util
from camera import blink_cam, picam
from door import bell
from messaging import receive_msg

from telepot.loop import MessageLoop
import telepot

import logging
import threading
import time

format = "%(asctime)s  -  %(name)s  -  %(funcName)s :        %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("fdia")


def thread_setup_door_bell(bot: object, blink: object, auth: object) -> None:
    """
    Door bell watch thread.


    :param bot: Telegram class instance object
    :type bot: object
    :param blink: Blink cam class instance object
    :type blink: object
    :param auth: Blink cam Authentication class instance object
    :type auth: object
    """
    time.sleep(15)
    logger.debug("create door class instance")
    watch_bell = bell.Door(bot, blink, auth)
    logger.debug("calling watch door bell ring function")
    watch_bell.ring()
    logger.debug("end door bell ring watch")


def thread_setup_receive_messages(bot: object, blink: object, auth: object) -> None:
    """
    Telegram receive messages thread setup

    :param bot: Telegram class instance object
    :type bot: object
    :param blink: Blink cam class instance object
    :type blink: object
    :param auth: Blink cam Authentication class instance object
    :type auth: object
    """
    logger.debug("create telegram class instance")
    telegram_messages = receive_msg.TelegramMessages(bot, blink, auth)
    logger.info("start Telegram Bot receiving messages")
    MessageLoop(bot, telegram_messages.handle_received_message).run_as_thread()


def main():
    """Main Program flow"""
    logger.info("Start Main Program")

    logger.debug("create config class instance")
    config = config_util.Configuration()
    logger.debug("creating blink instances")
    (blink_authentication_success, blink, auth) = blink_cam.start_blink_session(
        config.blink_config_file, config.blink_username, config.blink_password
    )
    logger.debug("creating telegram bot instance")
    bot = telepot.Bot(config.telegram_token)

    logger.debug("preparing door bell watch thread")
    door_bell_watcher = threading.Thread(
        target=thread_setup_door_bell, args=(bot, blink, auth)
    )

    logger.debug("calling - thread_setup_receive_messages - function")
    thread_setup_receive_messages(bot, blink, auth)

    logger.info("start thread monitoring door bell")
    door_bell_watcher.start()


if __name__ == "__main__":
    """
    Python main program start
    """
    main()
