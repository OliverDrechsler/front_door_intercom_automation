from __future__ import annotations
import yaml
import os
import logging
import io
import base64

logger = logging.getLogger('config')


class YamlReadError(Exception):
    """Exception raised for config yaml file read error.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message="A YAML config file readerror" +
                 " is occured during parsing file"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


class Configuration:
    """Reads gerneral yaml Config file into class."""

    def __init__(self) -> None:
        """Initial class definition.
        
        Read from config.yaml file it configuration into class attribute
        config dict and from there into multiple attributes.
        :return: Nothing adds class instance attribues
        :rtype: None
        """
        self.logger = logging.getLogger('config')
        self.base_path = self.get_base_path()
        self.config_file = self.define_config_file()
        self.config = self.read_config(self.config_file)
        self.telegram_token = self.config["telegram"]['token']
        self.telegram_chat_nr = self.config["telegram"]['chat_number']
        self.allowed_user_ids = self.config["telegram"]['allowed_user_ids']
        self.otp_password = self.config["otp"]['password']
        self.otp_length = self.config["otp"]['length']
        self.otp_interval = self.config["otp"]['interval']
        self.hash_type = self.config["otp"]['hash_type']
        self.door_bell = self.config["GPIO"]['door_bell_port']
        self.door_summer = self.config["GPIO"]['door_opener_port']
        self.blink_username = self.config["blink"]["username"]
        self.blink_password = self.config["blink"]["password"]
        self.blink_name = self.config["blink"]["name"]
        self.blink_config_file = self.base_path + self.config["blink"]["config_file"]
        self.common_image_path = self.config["common"]["image_path"]
        self.common_camera_type = self.config["common"]["camera_type"]
        self.picam_url = self.config["picam"]["url"]
        self.picam_image_width = self.config["picam"]["image_width"]
        self.picam_image_hight = self.config["picam"]["image_hight"]
        self.picam_image_filename = self.config["picam"]["image_filename"]
        self.picam_exposure = self.config["picam"]["exposure"]
        self.picam_rotation = self.config["picam"]["rotation"]
        self.picam_iso = self.config["picam"]["iso"]
        self.run_on_raspberry = self.config["common"]["run_on_raspberry"]

    def get_base_path(self) -> None:
        """
        Get from fdia base path. This normally one folder
        up from the config_util.py
        """
        return os.path.dirname(os.path.dirname(
                            os.path.abspath(__file__))) + "/"

    def read_config(self, config_file: str) -> None:
        """
        Reads config.yaml file into variables.

        :params config_file: the config file to be read
        :type config_file: string
        :return: Noting - adds class attribute self.config dictionary
          from config yaml file
        :rtype: None
        """
        self.logger.debug("reading config {0} file info dict"
                          .format(config_file))
        try:
            with open(file=config_file, mode='r') as file:
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

        if os.path.isfile(self.base_path + 'config.yaml'):
            return (self.base_path + 'config.yaml')
        else:
            self.logger.info("No config.yaml file detected. Using" + 
                             " temeplate one.")
            if not os.path.exists(self.base_path + 'config_template.yaml'):
                raise (NameError("No config file found!"))
            return (self.base_path + 'config_template.yaml')
        
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
        with open(self.base_path + 'config.yaml', 'w') as yaml_file:
            self.config["otp"]['password'] = self.base32_encode_totp_password(new_password)
            yaml.dump(self.config, yaml_file, default_flow_style=False)
            
        
