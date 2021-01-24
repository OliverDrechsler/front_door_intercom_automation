from __future__ import annotations
from common.config_util import Configuration
from camera import blink_cam, picam
from messaging import send_msg
import logging
import time
from gpiozero import Button


import datetime
config = Configuration()

logger = logging.getLogger('door-bell')

class Door(Configuration):
    """Front door subclass of configuration config watches the door bell and triggers
       sends telegram message and camera photo.
    """

    def __init__(self, bot: object, blink_instance: object, blink_auth_instance: object) -> None:
        """
        Initial class definition.
        
        Reads from parent class config.yaml file its configuration into class attribute
        config dict and from there into multiple attributes.
        :param blink_instance: blink class instance object
        :type blink_instance: class object
        :param telegram_instance: telegram bot class instance
        :type telegram_instance: class object
        :return: Nothing adds class instance attribues
        :rtype: None
        """
        self.logger = logging.getLogger('door-bell')
        self.logger.info("reading config")
        Configuration.__init__(self)
        self.bot = bot
        self.blink = blink_instance
        self.auth = blink_auth_instance

    def ring(self) -> None:
        """
        Watcher for door bell ring.

        :param self.door_bell: class attribute door_bell_port
        :type self.door_bell: int
        :param self.telegram_token:
        :param self.telegram_chat_nr:
        :return: Nothing
        :rtype: None
        """
        if self.is_raspberry_pi:
            button = Button(self.door_bell)

        self.logger.debug("starting endless loop watching door bell ring")
        while True:
            time.sleep(0.01)
            if self.is_raspberry_pi:     
                if button.is_pressed:
                    time.sleep(0.1)
                    if button.is_pressed:
                        self.logger.info("Door bell ringing")
                        send_msg.telegram_send_message(
                            self.bot,
                            self.telegram_chat_nr,
                            "Die Haustür hat geklingelt!" +
                            str(datetime.datetime.now()))
                        self.choose_camera()
                        time.sleep(5)
    
    def choose_camera(self) -> None:
        """
        Call choosen camera type from config file to take a foto.

        :param self.common_camera_type: camera type from config file
        :rtype self.common_camera_type: string
        :return: Nothing
        :rtype: None
        """
        if self.common_camera_type == "blink":
            self.blink_take_photo()
        elif self.common_camera_type == "picam":
            self.picam_take_photo()

    def blink_take_photo(self) -> None:
        """
        Use Blink camera to take a foto.

        :param self.blink: blink class instance
        :type self.blink: class object
        :param self.common_image_path: local image file path
        :type self.common_image_path: string
        :param self.telegram_token: telegram authentication token
        :type self.telegram_token: string
        :param self.telegram_chat_nr: telegramchat group id send message to
        :type self.telegram_chat_nr: string
        :return: Nothing
        :rtype: None
        """
        try:
            # request_take_foto()
            #request_download_foto()
            self.logger.info("trigger to take a snapshot")
            blink_cam.blink_snapshot(
                self.blink, 
                self.blink_name, 
                self.common_image_path)
            send_msg.telegram_send_photo(
                self.bot, 
                self.telegram_chat_nr, 
                self.common_image_path)
        except:
            pass
        
    def picam_take_photo(self) -> None:
        """
        Use PiCam camera to take a foto.

        :param self.picam_url: PiCam URL to call REST API
        :type self.picam_url: string
        :param self.picam_image_width: foto width
        :type self.picam_image_width: int
        :param self.picam_image_hight: foto hight
        :type self.picam_image_hight: int
        :param self.picam_image_filename: PiCam foto filename
        :type self.picam_image_filename: string
        :param self.picam_exposure: auto, night....
        :type self.picam_exposure: string
        :param self.picam_rotation: picture rotation in degrees
        :type self.picam_rotation: int
        :param self.picam_iso: foto iso number
        :type self.picam_iso: int
        :param self.common_image_path: local image file path
        :type self.common_image_path: string
        :param self.telegram_token: telegram authentication token
        :type self.telegram_token: string
        :param self.telegram_chat_nr: telegramchat group id send message to
        :type self.telegram_chat_nr: string
        :return: Nothing
        :rtype: None
        """
        try:
            self.logger.info("trigger to take a snapshot")
            picam.request_take_foto(
                self.picam_url, 
                self.picam_image_width, 
                self.picam_image_hight, 
                self.picam_image_filename, 
                self.picam_exposure,
                self.picam_rotation,
                self.picam_iso)
            picam.request_download_foto(
                self.picam_url,
                self.picam_image_filename,
                self.common_image_path
                )
            send_msg.telegram_send_photo(
                self.bot, 
                self.telegram_chat_nr, 
                self.common_image_path)
        except:
            pass