from __future__ import annotations
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth
from blinkpy.helpers.util import json_load
import logging
import time
import os
import json

logger = logging.getLogger("blink_cam")


def start_blink_session(
    blink_config_file: str, blink_username, blink_password
) -> (bool, object, object):
    """Starts a blink cam session

    :param blink_config_file: blink session config file path
    :type blink_config_file: string
    :param blink_username: blink username
    :type blink_username: string
    :param blink_password: blink password
    :type blink_password: string
    :return: authentication_success for existing session or 2FA token required, blink instance, auth instance
    :rtype authentication_success: boolean
    :rtype blink: class
    :rtype auth: class
    """
    blink = Blink(refresh_rate=3)

    if os.path.exists(blink_config_file):
        logger.info("using existing blink_config.json")
        auth = Auth(json_load(blink_config_file), no_prompt=True)
        authentication_success = True
    else:
        logger.info(
            "no blink_config.json found - 2FA " + "authentication token required"
        )
        auth = Auth(
            {"username": blink_username, "password": blink_password}, no_prompt=True
        )
        authentication_success = None

    blink.auth = auth
    opts = {"retries": 10, "backoff": 2}
    blink.auth.session = blink.auth.create_session(opts=opts)
    try:
        logger.info("start blink session")
        blink.start()
    except Exception as err:
        logger.info("blink session exception occured: {0}".format(err))
        pass

    return authentication_success, blink, auth


def blink_snapshot(blink: object, blink_name: str, image_path: str) -> None:
    """Creates a new blink cam snapshot and downloads it.

    :param blink: blink class instance
    :type blink: class instance
    :param blink_name: blink camera name
    :type blink_name: string
    :param image_path: local image file path
    :type image_path: str
    :return: Nothing
    :rtype: None
    """
    logger.info(
        "i'll take a snapshot from cam {0} and store it here {1}".format(
            blink_name, image_path
        )
    )

    try:
        logger.debug("create a camera instance")
        camera = blink.cameras[blink_name]
    except Exception as err:
        logger.info("Error: {0}".format(err))
        pass

    logger.debug("take a snpshot")
    camera.snap_picture()  # Take a new picture with the camera
    logger.debug("refresh blink server info")
    time.sleep(3)  # wait for blink class instane refresh invterval to be done
    blink.refresh()  # refesh Server info
    if os.path.exists(image_path):
        logger.debug("a file already exists and will be deteleted before hand")
        os.remove(image_path)
    logger.info("saving blink foto")
    camera.image_to_file(image_path)
    return None


def add_2fa_blink_token(token: str, blink: object, auth: object) -> bool:
    """Adds a required 2FA token to blink session.

    :param token: required 2FA token
    :type token: str
    :param blink: blink class instance
    :type blink: class instance
    :param auth: blink auth class instance
    :type auth: class instance
    :return: success True
    :rtype: boolean
    """
    logger.debug("add a 2FA token for authentication")
    auth.send_auth_key(blink, token)
    logger.debug("verify 2FA token")
    blink.setup_post_verify()
    logger.info("added 2FA token " + token)
    return True


def save_blink_config(blink: object, blink_config_file: str) -> bool:
    """Saves an existing blink session into a config file.

    This save a bink session for reuse on device with already
    authenticated token into a config file.

    :param blink: blink class instance
    :type blink: class instance
    :param blink_config_file: blink config file path
    :type blink_config_file: str
    :return: success True
    :rtype: boolean
    """
    logger.info("saving blink authenticated session infos into config file")
    blink.save(blink_config_file)
    return True


def delete_blink_config(blink: object, auth: object, blink_config_file: str) -> bool:
    """Deletes a blink config file and existing class instances

    :param blink: blink class instance
    :type blink: class instance
    :param auth: auth class instance
    :type auth: class instance
    :param blink_config_file: blink session config file path
    :type blink_config_file: str
    :return: success True
    :rtype: bool
    """
    if os.path.exists(blink_config_file):
        os.remove(blink_config_file)
        logger.debug("deleted blink config file")
    logger.debug("deleting blink and auth class instances")
    del blink
    del auth
    logger.info("deleted blink class instances and config")
    return True


def blink_json_load(blink_config_file: str,) -> object:
    """Load blink json credentials from file.
    
    :params blink_config_file: blink config file name
    :type blink_config_file: str
    :return: blink_json_data dict object
    :rtype: object
    """
    logger.debug("load blink config file")
    try:
        with open(blink_config_file, "r") as json_file:
            blink_json_data = json.load(json_file)
        return blink_json_data
    except FileNotFoundError:
        logger.error("Could not find %s", blink_config_file)
    except json.decoder.JSONDecodeError:
        logger.error("File %s has improperly formatted json", blink_config_file)
    return None


def blink_compare_config(
    auth: object, blink: object, config_class_instance: object
) -> bool:
    """
    Compares Blink actual class config with blink config file
    and stores it in case of difference.
    Blink will daily update the device token.
    Therefore we have to update the config file

    :params auth: blink auth class instance
    :type auth: class instance object
    :params blink: blibk class instance 
    :type blink: class instance object
    :params config_class_instance: config class instance object
    :type config_class_instance: class instance object
    :return: success status
    :rtype: boolean
    """
    blink_json_data = blink_json_load(config_class_instance.blink_config_file)
    if auth.login_attributes != blink_json_data:
        logger.debug("saved blink config file differs from running config")
        logger.debug("blink config object = {0}".format(auth.login_attributes))
        logger.debug("blink config file   = {0}".format(blink_json_data))
        logger.info("will update blink config file")
        save_blink_config(blink, config_class_instance.blink_config_file)
        return True
    else:
        logger.debug("saved blink config file == running config")
        return False
