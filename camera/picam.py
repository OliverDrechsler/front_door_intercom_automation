from __future__ import annotations
import requests
import logging
import os
import json

logger = logging.getLogger('PiCam')

def request_take_foto(
    picam_url: str, 
    picam_image_width: int, 
    picam_image_hight: int, 
    picam_image_filename: str, 
    picam_exposure: str, 
    picam_rotation: int, 
    picam_iso: int) -> int:
    """Take a photo from PiCam

    This creates a new snapshot via PiCam REST-API with a
    POST request.

    :param picam_url: PiCam URL with protocol
    :type picam_url: str
    :param picam_image_width: image width size
    :type picam_image_width: int
    :param picam_image_hight: image hight size
    :type picam_image_hight: int
    :param picam_image_filename: image filename to store at PiCam
    :type picam_image_filename: str
    :param picam_exposure: PiCam camera expore mode auto,night,...
    :type picam_exposure: str
    :param picam_rotation: Image rotation degrees
    :type picam_rotation: int
    :param picam_iso: image iso mode
    :type picam_iso: int
    :return: http request status code
    :rtype: int
    """
    logger.info("start take a snapshot")
    payload = {
        "rotation": picam_rotation,
        "width": picam_image_width,
        "filename": picam_image_filename,
        "hight": picam_image_hight,
        "exposure": picam_exposure,
        "iso": picam_iso
    }
    headers = {'content-type': 'application/json'}
    r = requests.post(picam_url,
                      data=json.dumps(payload), headers=headers)
    logger.debug("make a snapshot ended with status {}".format(r.status_code))
    logger.info("end take snapshot")
    return r.status_code


def request_download_foto(
    picam_url: str,
    picam_image_filename: str,
    local_image_path: str) -> int:
    """Downloads a Photo via GET request from PiCAM REST-API

    :param picam_url: PiCam URL with protocol
    :type picam_url: str
    :param picam_image_filename: image filename to store at PiCam
    :type picam_image_filename: str
    :param local_image_path: local image path with filename
    :type local_image_path: str
    :return: http request status code
    :rtype: int
    """
    logger.info("start downloading foto")
    if os.path.exists(local_image_path):
        logger.debug("deleting already existing file before hand")
        os.remove(local_image_path)

    with open(local_image_path, "wb") as file:
        response = requests.get(
            picam_url + "?filename=" + picam_image_filename)
        file.write(response.content)
    logger.debug(
        "downloading foto ended with status {}".format(
            response.status_code))
    logger.info("end downloading foto")
    return response.status_code
