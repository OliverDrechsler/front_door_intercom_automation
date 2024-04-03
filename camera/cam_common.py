from typing import Dict
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from datetime import datetime, timezone
from astral.sun import sun
from astral import LocationInfo
from camera import blink_cam, picam
from config import config_util
from bot import send_msg
import logging


logger: logging.Logger = logging.getLogger(name="cam_common")


def daylight_detected(config_class_instance: object) -> bool:
    """detect daylight if config param is set / enabled

    :param config_class_instance: config class instance object
    :type config_class_instance: class instance object
    :return: _description_
    :rtype: bool
    """
    logger.debug(msg="Daylight detection is enabled " + f"{config_class_instance.enable_detect_daylight}")
    if (config_class_instance.enable_detect_daylight):
        loc = LocationInfo(name="Berlin", region="Germany", timezone="Europe/Berlin")
        time_now: datetime = datetime.now(tz=timezone.utc)
        s: Dict[str, datetime] = sun(observer=loc.observer, date=time_now, tzinfo=loc.timezone)
        daylight: bool = (s['sunrise'] <= time_now <= (s['sunset']))
        logger.info(msg=f"Is daylight detected: {daylight}")
        return daylight
    return False


def choose_camera(auth: Auth, blink: Blink,
                  config_class_instance: config_util.Configuration) -> bool:
    """
    Call choosen camera type from config file to take a foto.

    :param auth: blink cam authentication class instance
    :type auth: class instance object
    :param blink: blink cam class instance
    :type blink: class instance object
    :param config_class_instance: config class instance object
    :type config_class_instance: class instance object
    :return: success boolean
    :rtype: bool
    """
    logger.debug(msg="choose camera")
    if (daylight_detected(config_class_instance=config_class_instance)):
        return picam_take_photo(auth=auth, blink=blink, config_class_instance=config_class_instance)

    if config_class_instance.common_camera_type == "blink":
        logger.debug(msg="blink cam choosen")
        return blink_take_photo(auth=auth, blink=blink, config_class_instance=config_class_instance)
    elif config_class_instance.common_camera_type == "picam":
        logger.debug(msg="PiCam choosen")
        return picam_take_photo(auth=auth, blink=blink, config_class_instance=config_class_instance)


def blink_take_photo(
    auth: Auth, blink: Blink, config_class_instance: config_util.Configuration, retry=1
) -> bool:
    """
    Use Blink camera to take a foto.
    If failed retry with PiCam

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
        logger.info(msg="take a Blink Cam snapshot")
        blink_cam.blink_snapshot(
            blink=blink,
            blink_name=config_class_instance.blink_name,
            image_path=config_class_instance.common_image_path,
        )

        blink_cam.blink_compare_config(auth=auth, blink=blink, config_class_instance=config_class_instance)

        send_msg.telegram_send_photo(
            bot=config_class_instance.bot,
            telegram_chat_nr=config_class_instance.telegram_chat_nr,
            common_image_path=config_class_instance.common_image_path,
        )
        return True
    except:
        logger.info(msg="blink cam take snapshot - error occured")
        send_msg.telegram_send_message(
            bot=config_class_instance.bot,
            telegram_chat_nr=config_class_instance.telegram_chat_nr,
            message="Blink Cam take snapshot - error occured",
        )
        if retry < 2:
            logger.info(msg="second try with picam now")
            picam_take_photo(auth=auth, blink=blink, config_class_instance=config_class_instance, retry=2)
        return False


def picam_take_photo(
    auth: Auth, blink: Blink, config_class_instance: config_util.Configuration, retry=1
) -> bool:
    """
    Use PiCam camera to take a foto.
    If failed retry with blink cam

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
        logger.info(msg="take a PiCam snapshot")
        if (
            picam.request_take_foto(
                picam_url=config_class_instance.picam_url,
                picam_image_width=config_class_instance.picam_image_width,
                picam_image_hight=config_class_instance.picam_image_hight,
                picam_image_filename=config_class_instance.picam_image_filename,
                picam_exposure=config_class_instance.picam_exposure,
                picam_rotation=config_class_instance.picam_rotation,
                picam_iso=config_class_instance.picam_iso,
            )
            != 200
        ):
            raise NameError("HTTP Status not 200")
        if (
            picam.request_download_foto(
                picam_url=config_class_instance.picam_url,
                picam_image_filename=config_class_instance.picam_image_filename,
                local_image_path=config_class_instance.common_image_path,
            )
            != 200
        ):
            raise NameError("HTTP Status not 200")
        send_msg.telegram_send_photo(
            bot=config_class_instance.bot,
            telegram_chat_nr=config_class_instance.telegram_chat_nr,
            common_image_path=config_class_instance.common_image_path,
        )
        return True
    except:
        logger.debug(msg="PiCam take snapshot - error occured")
        send_msg.telegram_send_message(
            bot=config_class_instance.bot,
            telegram_chat_nr=config_class_instance.telegram_chat_nr,
            message="PiCam take snapshot - error occured",
        )
        if retry < 2:
            logger.info(msg="second try with blink now")
            blink_take_photo(auth=auth, blink=blink, config_class_instance=config_class_instance, retry=2)
        return False
