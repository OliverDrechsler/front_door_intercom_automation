from __future__ import annotations

import base64
import logging
import os
from collections import ChainMap

import telebot
import yaml

from config.default_cam_enum import DefaultCam
from config.yaml_read_error import YamlReadError

logger = logging.getLogger("config")


class Configuration:
    """Reads gerneral yaml Config file into class."""

    def __init__(self) -> None:
        """Initial class definition.

        Read from config.yaml file it configuration into class attribute
        config dict and from there into multiple attributes.
        :return: Nothing adds class instance attribues
        :rtype: None
        """
        self.logger = logging.getLogger("config")
        self.base_path = self.get_base_path()
        self.config_file = self.define_config_file()
        self.config = self.read_config(self.config_file)

        self.bot: telebot.TeleBot = None

        self.telegram_token: str = self.config["telegram"]["token"]
        self.telegram_chat_nr = self.config["telegram"]["chat_number"]
        self.allowed_user_ids = self.config["telegram"]["allowed_user_ids"]

        self.otp_password: str = self.config["otp"]["password"]
        self.otp_length: int = self.config["otp"]["length"]
        self.otp_interval: int = self.config["otp"]["interval"]
        self.hash_type: str = self.config["otp"]["hash_type"]

        self.run_on_raspberry: bool = self.config["GPIO"]["run_on_raspberry"]
        self.door_bell: int = self.config["GPIO"]["door_bell_port"]
        self.door_bell_enabled: bool = self.config["GPIO"]["enable_door_bell_port"]
        self.door_bell_bounce_time: int = self.config["GPIO"]["door_bell_bounce_time"]
        self.door_summer: int = self.config["GPIO"]["door_opener_port"]
        self.door_summer_enabled: bool = self.config["GPIO"]["enable_door_opener_port"]
        self.testing_bell_msg: bool = self.config["GPIO"]["testing_msg"]

        self.photo_image_path: str = self.config["photo_general"]["image_path"]
        self.default_camera_type = DefaultCam(self.config["photo_general"]["default_camera_type"].upper())
        self.enable_detect_daylight: bool = self.config["photo_general"]["enable_detect_daylight"]
        self.timezone: str = self.config["photo_general"]["timezone"]
        self.location: str = self.config["photo_general"]["location"]
        self.lat: float = self.config["photo_general"].get("lat", None)  # optional value see config_template.yaml for more information
        self.lon: float = self.config["photo_general"].get("lat", None)  # optional value see config_template.yaml for more information
        self.image_brightness: float = self.config["photo_general"].get("brightness_enhancer", None)  # optional value see config_template.yaml for more information
        self.image_contrast: float = self.config["photo_general"].get("contrast_enhancer", None)  # optional value see config_template.yaml for more information

        self.blink_enabled: bool = self.config["blink"]["enabled"]
        self.blink_username: str = self.config["blink"]["username"]
        self.blink_password: str = self.config["blink"]["password"]
        self.blink_name: str = self.config["blink"]["name"]
        self.blink_config_file: str = self.base_path + self.config["blink"]["config_file"]
        self.blink_night_vision: bool = self.config["blink"]["night_vision"]
        self.blink_image_brightening: bool = self.config["blink"].get("image_brightening", False) # optional value see config_template.yaml for more information

        self.picam_enabled: bool = self.config["picam"]["enabled"]
        self.picam_url: str = self.config["picam"]["url"]
        self.picam_image_width: int = self.config["picam"]["image_width"]
        self.picam_image_hight: int = self.config["picam"]["image_hight"]
        self.picam_image_filename: str = self.config["picam"]["image_filename"]
        self.picam_exposure: str = self.config["picam"]["exposure"]
        self.picam_rotation: int = self.config["picam"]["rotation"]
        self.picam_iso: int = self.config["picam"]["iso"]
        self.picam_night_vision: bool = self.config["picam"]["night_vision"]
        self.picam_image_brightening: bool = self.config["picam"].get("image_brightening", False)  # optional value see config_template.yaml for more information

        self.web_user_dict: dict[str, str] = self.get_web_user_dict()
        self.flask_enabled: bool = self.config["web"]["enabled"]
        self.flask_web_host: int = self.config["web"]["flask_web_host"]
        self.flask_web_port: int = self.config["web"]["flask_web_port"]
        self.flask_secret_key: str = self.config["web"]["flask_secret_key"]
        self.flask_browser_session_cookie_lifetime: int = self.config["web"]["browser_session_cookie_lifetime"]

    def get_web_user_dict(self) -> dict:
        """Get user dict from list of yaml telegram.list

        :return: dict of user key and values of telegram id
        :rtype: dict
        """
        return dict(ChainMap(*self.config["web"]["flask_users"]))

    def get_base_path(self) -> None:
        """
        Get from fdia base path. This normally one folder
        up from the config_util.py
        """
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/"

    def read_config(self, config_file: str) -> None:
        """
        Reads config.yaml file into variables.

        :params config_file: the config file to be read
        :type config_file: string
        :return: Noting - adds class attribute self.config dictionary
          from config yaml file
        :rtype: None
        """
        self.logger.debug("reading config {0} file info dict".format(config_file))
        try:
            with open(file=config_file, mode="r") as file:
                return yaml.load(file, Loader=yaml.SafeLoader)
        except FileNotFoundError:
            self.logger.error("Could not find %s", self.config_file)
            raise FileNotFoundError("Could not find config file")
        except:
            self.logger.error("a YAML error is occured during parsing file %s ", self.config_file)
            raise YamlReadError("a YAML error is occured during parsing file")

    def define_config_file(self) -> None:
        """
        Checks and defines Config yaml file path.

        :return: adds a new class path attribute for the config file.
        :rtype: None
        """
        self.logger.debug("checking if config.yaml file exists")

        if os.path.isfile(self.base_path + "config.yaml"):
            return self.base_path + "config.yaml"

        self.logger.info("No config.yaml file detected. Using" + " temeplate one.")
        if not os.path.exists(self.base_path + "config_template.yaml"):
            raise (NameError("No config file found!"))
        return self.base_path + "config_template.yaml"

    def base32_encode_totp_password(self, new_password):
        """
        Encodes a new provided password into BASE32 string

        :param new_password: new provided TOTP ASCII password
        :type new_password: string
        """
        return (base64.b32encode(new_password.upper().encode("UTF-8"))).decode("UTF-8")

    def write_yaml_config(self, new_password):
        """Writes or updates the config.yaml file with the new provided TOTP password

        :param new_password: new provided TOTP ASCII password
        :type new_password: string
        """
        with open(self.base_path + "config.yaml", "w") as yaml_file:
            self.config["otp"]["password"] = self.base32_encode_totp_password(new_password)
            yaml.dump(self.config, yaml_file, default_flow_style=False)
