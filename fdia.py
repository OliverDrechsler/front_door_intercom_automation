#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from argparse import ArgumentParser
from config import config_util
from camera import blink_cam
from door import bell
from bot import receive_msg
import telebot
import logging
import threading
import time
import sys

"""Define code logging"""
default_log_level = logging.INFO

format = "%(asctime)s  -  %(name)s  -  %(funcName)s :        %(message)s"
logging.basicConfig(format=format, level=default_log_level, datefmt="%Y-%m-%d %H:%M:%S")
logger: logging.Logger = logging.getLogger(name="fdia")

allowed_levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}
logging_argparse = ArgumentParser(prog=__file__, add_help=True)
logging_argparse.add_argument(
    "-l",
    "--log-level",
    default=f"{logging.getLevelName(default_log_level)}",
    choices=allowed_levels,
    help="set log level",
)
logging_args, _ = logging_argparse.parse_known_args(args=sys.argv[1:])
log_level = allowed_levels.get(logging_args.log_level.lower())
try:
    logging.getLogger().setLevel(level=log_level)
except Exception:
    logging.error(msg=f"Invalid log level retrieved from command line {logging_args.log_level}")
    pass

actual_log_level = logging.getLevelName(level=logger.getEffectiveLevel())
logger.info(msg=f"set logging level to: {actual_log_level}")
if actual_log_level is not logging.INFO:
    telebot.logger.setLevel(level=actual_log_level)


def thread_setup_door_bell(bot, blink, auth) -> None:
    """
    Door bell watch thread.


    :param bot: Telegram class instance object
    :type telebot.TeleBot: object
    :param blink: Blink cam class instance object
    :type Blink: object
    :param auth: Blink cam Authentication class instance object
    :type Auth: object
    """
    time.sleep(15)
    logger.debug(msg="create door class instance")
    watch_bell = bell.Door(bot=bot, blink=blink, auth=auth)
    logger.debug(msg="calling watch door bell ring function")
    watch_bell.ring()
    logger.debug(msg="end door bell ring watch")


def main() -> None:
    """Main Program flow"""
    logger.info(msg="Start Main Program")

    logger.debug(msg="create config class instance")
    config = config_util.Configuration()
    logger.debug(msg="creating blink instances")
    (blink_authentication_success, blink, auth) = blink_cam.start_blink_session(
        blink_config_file=config.blink_config_file, blink_username=config.blink_username, blink_password=config.blink_password
    )

    logger.debug(msg="initialize telegram bot instance")
    bot = telebot.TeleBot(token=config.telegram_token, parse_mode=None)
    config.bot = bot
    
    logger.debug(msg="preparing door bell watch thread")
    door_bell_watcher = threading.Thread(
        target=thread_setup_door_bell, args=(bot, blink, auth)
    )

    logger.info(msg="start thread monitoring door bell")
    door_bell_watcher.start()

    logger.debug(msg="calling - thread_setup_receive_messages - function")
    logger.debug(msg="create telegram class instance")
    logger.info(msg="start Telegram Bot receiving messages")
    receive_msg.ReceivingMessage(bot=bot,
                                 config=config,
                                 blink_instance=blink,
                                 blink_auth_instance=auth).start()


if __name__ == "__main__":
    """
    Python main program start
    """
    main()
