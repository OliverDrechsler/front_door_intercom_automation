import yaml
import os
import logging

logger = logging.getLogger('config')

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
        self.define_config_file()
        self.read_config(self.config_file)
        self.telegram_token = self.config["telegram"]['token']
        self.telegram_chat_nr = self.config["telegram"]['chat_number']
        self.allowed_user_ids = self.config["telegram"]['allowed_user_ids']
        self.otp_password = self.config["otp"]['password']
        self.otp_length = self.config["otp"]['length']
        self.otp_interval = self.config["otp"]['interval']
        self.door_bell = self.config["GPIO"]['door_bell_port']
        self.door_summer = self.config["GPIO"]['door_opener_port']
        self.blink_username = self.config["blink"]["username"]
        self.blink_password = self.config["blink"]["password"]
        self.blink_name = self.config["blink"]["name"]
        self.blink_config_file = str(os.path.abspath('') + "/" + self.config["blink"]["config_file"])
        self.common_image_path = self.config["common"]["image_path"]
        self.common_camera_type = self.config["common"]["camera_type"]
        self.picam_url = self.config["picam"]["url"]
        self.picam_image_width = self.config["picam"]["image_width"]
        self.picam_image_hight = self.config["picam"]["image_hight"]
        self.picam_image_filename = self.config["picam"]["image_filename"]
        self.picam_exposure = self.config["picam"]["exposure"]
        self.picam_rotation = self.config["picam"]["rotation"]
        self.picam_iso = self.config["picam"]["iso"]

    def read_config(self, config_file: str) -> None:
        """
        Reads config.yaml file into variables.

        :params config_file: the config file to be read
        :type config_file: string
        :return: Noting - adds class attribute self.config dictionary from config yaml file
        :rtype: None
        """
        self.logger.debug("reading config {0} file info dict".format(config_file))
        with open(file=config_file, mode='r') as file:
            self.config = yaml.load(file, Loader=yaml.SafeLoader)

    def define_config_file(self) -> None:
        """
        Checks and defines Config yaml path.

        :return: adds a new class path attribute.
        :rtype: None
        """
        self.logger.info("checking if config.yaml file exists")
        if os.path.isfile(os.path.abspath('') + '/config.yaml'):
            self.config_file = (os.path.abspath('') + '/config.yaml')
        else:
            self.logger.info("a config files does not exist - using config template")
            self.config_file = (os.path.abspath('') + '/config_template.yaml')
    