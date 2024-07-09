#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import queue
import sys
import threading
import time
from argparse import ArgumentParser

import telebot

from bot import receive_msg, send_msg
from camera import camera
from config import config_util
from door import bell
from door.opener import DoorOpener
from web.web_door_opener import WebDoorOpener

"""Define code logging"""
default_log_level = logging.INFO

format = "%(asctime)s - %(name)s - %(threadName)s - %(funcName)s : %(message)s"
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


def run_web_app(shutdown_event: threading.Event, config: config_util.Configuration, loop, message_task_queue: queue.Queue,
                camera_task_queue_async: asyncio.Queue,
                door_open_task_queue: queue.Queue):
    global web_app
    web_app = WebDoorOpener(shutdown_event=shutdown_event, config=config,
                            loop=loop,
                            message_task_queue=message_task_queue,
                            camera_task_queue_async=camera_task_queue_async,
                            door_open_task_queue=door_open_task_queue)
    web_app.run()


def thread_open_door(shutdown_event: threading.Event, config: config_util.Configuration, loop, message_task_queue: queue.Queue,
                     door_open_task_queue: asyncio.Queue) -> None:
    logger.debug(msg="create door opener class instance")
    opener = DoorOpener(shutdown_event=shutdown_event, config=config, loop=loop, message_task_queue=message_task_queue,
                        door_open_task_queue=door_open_task_queue)
    logger.debug(msg="calling door opener start function")
    opener.start()
    logger.debug(msg="end door opener loop")


def thread_door_bell(shutdown_event: threading.Event, config: config_util.Configuration, loop,
                     message_task_queue: queue.Queue,
                     camera_task_queue_async: asyncio.Queue) -> None:
    """
    Door bell watch thread.
    """
    logger.debug(msg="create door class instance")
    watch_bell = bell.DoorBell(shutdown_event=shutdown_event,
                               config=config,
                               loop=loop,
                               message_task_queue=message_task_queue,
                               camera_task_queue_async=camera_task_queue_async)
    logger.debug(msg="calling watch door bell ring function")
    watch_bell.ring()
    logger.debug(msg="end door bell ring watch")


def thread_receive_telegram_msg(shutdown_event: threading.Event, config: config_util.Configuration, loop,
                                camera_task_queue_async: asyncio.Queue, door_open_task_queue: queue.Queue):
    logger.info(msg="start Telegram Bot receiving messages")
    receive_msg.ReceivingMessage(shutdown_event=shutdown_event,
                                 config=config,
                                 loop=loop,
                                 camera_task_queue_async=camera_task_queue_async,
                                 door_open_task_queue=door_open_task_queue
                                 ).start()


def thread_send_telegram_msg(shutdown_event: threading.Event, config: config_util.Configuration, loop,
                             message_task_queue: queue.Queue):
    logger.info(msg="start Telegram Bot SEND messages instance thread")
    send_msg.SendMessage(shutdown_event=shutdown_event,
                         config=config,
                         loop=loop,
                         message_task_queue=message_task_queue
                         ).start()


async def camera_task(shutdown_event: threading.Event, config: config_util.Configuration, loop,
                      camera_task_queue_async: asyncio.Queue, message_task_queue: queue.Queue):
    logger.info("Starting camera task")
    cam = camera.Camera(config=config, loop=loop, camera_task_queue_async=camera_task_queue_async,
                        message_task_queue=message_task_queue)
    while not shutdown_event.is_set():
        await cam.start()
        await asyncio.sleep(0.1)  # Small delay to prevent tight loop
    logger.info("Camera task shutdown complete")


def thread_cameras(shutdown_event: threading.Event, config: config_util.Configuration, loop,
                   camera_task_queue_async: asyncio.Queue, message_task_queue: queue.Queue):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(camera_task(shutdown_event, config, loop, camera_task_queue_async, message_task_queue))
    logger.info("Camera event loop shutdown complete")


def main() -> None:
    """Main Program flow"""
    logger.info(msg="Start Main Program")

    # Define a global shutdown flag
    shutdown_event = threading.Event()

    message_task_queue = queue.Queue()
    door_open_task_queue = queue.Queue()
    camera_task_queue_async = asyncio.Queue()

    logger.debug(msg="create config class instance")
    config = config_util.Configuration()

    logger.debug(msg="initialize telegram bot instance")
    bot = telebot.TeleBot(token=config.telegram_token, parse_mode=None)
    config.bot = bot

    logger.debug("creating camera thread with asyncio")
    loop = asyncio.new_event_loop()
    camera_thread_async = threading.Thread(target=thread_cameras,
                                           args=(
                                               shutdown_event, config, loop, camera_task_queue_async,
                                               message_task_queue))
    logger.info("start camera thread")
    camera_thread_async.start()

    logger.debug("creating Telegram Bot SEND thread")
    send_msg_thread = threading.Thread(
        target=thread_send_telegram_msg, args=(shutdown_event, config, loop, message_task_queue))
    logger.info("start Telegram Bot SEND thread")
    send_msg_thread.start()

    logger.debug("creating Telegram Bot receiving thread")
    receive_msg_thread = threading.Thread(
        target=thread_receive_telegram_msg,
        args=(shutdown_event, config, loop, camera_task_queue_async, door_open_task_queue))
    logger.info("start Telegram Bot receiving thread")
    receive_msg_thread.start()

    logger.debug(msg="preparing door bell watch thread")
    door_bell_thread = threading.Thread(
        target=thread_door_bell, args=(shutdown_event, config, loop, message_task_queue, camera_task_queue_async)
    )
    logger.info(msg="start thread monitoring door bell")
    door_bell_thread.start()

    logger.debug(msg="preparing door open thread")
    door_opener_thread = threading.Thread(
        target=thread_open_door, args=(shutdown_event, config, loop, message_task_queue, door_open_task_queue)
    )
    logger.info(msg="start door open thread")
    door_opener_thread.start()

    logger.debug(msg="preparing flask web door opener")
    web_thread = threading.Thread(target=run_web_app, args=(
        shutdown_event, config, loop, message_task_queue, camera_task_queue_async, door_open_task_queue))
    logger.info(msg="start thread flask web door opener")
    web_thread.start()

    try:
        while True:
            time.sleep(0.01)  # Keep the main thread alive

    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt received")

        logger.info("Shutting down...")
        shutdown_event.set()

        message_task_queue.put(None)
        door_open_task_queue.put(None)
        asyncio.run_coroutine_threadsafe(camera_task_queue_async.put(None), loop)

        send_msg_thread.join()
        door_opener_thread.join()
        camera_thread_async.join()
        receive_msg_thread.join()
        logger.info("shutdown door_bell_thread")
        door_bell_thread.join()
        logger.info("shutdown web_thread")
        global web_app
        web_app.shutdown()
        web_thread.join()

        os._exit(0)


if __name__ == "__main__":
    """
    Python main program start
    """
    main()
