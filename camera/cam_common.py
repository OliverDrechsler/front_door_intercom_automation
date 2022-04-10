from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load
from camera import blink_cam, picam
from messaging import send_msg
import logging


logger = logging.getLogger('cam_common')

def choose_camera(auth: object, blink: object, config_class_instance: object) -> None:
    """
    Call choosen camera type from config file to take a foto.

    :param auth: blink cam authentication class instance
    :type auth: class instance object
    :param blink: blink cam class instance
    :type blink: class instance object
    :param config_class_instance: config class instance object
    :type config_class_instance: class instance object
    :return: Nothing
    :rtype: None
    """
    logger.debug("choose camera")
    if config_class_instance.common_camera_type == "blink":
        logger.debug("blink cam choosen")
        result = blink_take_photo(auth, blink, config_class_instance)
        return bool(result)
    elif config_class_instance.common_camera_type == "picam":
        logger.debug("PiCam choosen")
        result = picam_take_photo(auth, blink, config_class_instance)
        return bool(result)

def blink_take_photo(auth: object, blink: object, config_class_instance: object, retry=1) -> bool:
    """
    Use Blink camera to take a foto.

    :param auth: blink cam authentication class instance
    :type auth: class instance object
    :param blink: blink cam class instance
    :type blink: class instance object
    :param config_class_instance: config class instance object
    :type config_class_instance: class instance object
    :param retry: retry count if take photo error occurs, default = 1
    :type retry: int 
    :return: success status
    :rtype: boolean
    """
    try:
        logger.info("take a Blink Cam snapshot")
        blink_cam.blink_snapshot(
            blink, 
            config_class_instance.blink_name, 
            config_class_instance.common_image_path)
        
        blink_cam.blink_compare_config(auth, blink, config_class_instance)
        
        send_msg.telegram_send_photo(
            config_class_instance.bot, 
            config_class_instance.telegram_chat_nr, 
            config_class_instance.common_image_path)
        return True
    except:
        logger.info("blink cam take snapshot - error occured")
        send_msg.telegram_send_message(
            config_class_instance.bot, 
            config_class_instance.telegram_chat_nr, 
            "Blink Cam take snapshot - error occured")            
        if retry < 2:
            logger.info("second try with picam now")
            picam_take_photo(auth, blink, config_class_instance, retry=2)
        return False

def picam_take_photo(auth: object, blink: object, config_class_instance: object, retry=1) -> bool:
    """
    Use PiCam camera to take a foto.

    :param auth: blink cam authentication class instance
    :type auth: class instance object
    :param blink: blink cam class instance
    :type blink: class instance object
    :param config_class_instance: config class instance object
    :type config_class_instance: class instance object
    :param retry: retry count if take photo error occurs, default = 1
    :type retry: int 
    :return: success status
    :rtype: boolean
    """
    try:
        logger.info("take a PiCam snapshot")
        if picam.request_take_foto(
                config_class_instance.picam_url, 
                config_class_instance.picam_image_width, 
                config_class_instance.picam_image_hight, 
                config_class_instance.picam_image_filename, 
                config_class_instance.picam_exposure,
                config_class_instance.picam_rotation,
                config_class_instance.picam_iso) != 200:
            raise NameError('HTTP Status not 200')
        if picam.request_download_foto(
                config_class_instance.picam_url,
                config_class_instance.picam_image_filename,
                config_class_instance.common_image_path
                ) != 200:
            raise NameError('HTTP Status not 200')
        send_msg.telegram_send_photo(
            config_class_instance.bot, 
            config_class_instance.telegram_chat_nr, 
            config_class_instance.common_image_path)
        return True
    except:
        logger.debug("PiCam take snapshot - error occured")
        send_msg.telegram_send_message(
            config_class_instance.bot, 
            config_class_instance.telegram_chat_nr, 
            "PiCam take snapshot - error occured")            
        if retry < 2:
            logger.info("second try with blink now")
            blink_take_photo(auth, blink, config_class_instance, retry=2)
        return False
