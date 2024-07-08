from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import time
from datetime import datetime, timezone

import aiohttp
import requests
from astral import LocationInfo
from astral.sun import sun
from blinkpy.auth import Auth
from blinkpy.blinkpy import Blink
from blinkpy.helpers.util import json_load

from config.config_util import Configuration, DefaultCam
from config.data_class import Camera_Task, Message_Task

logger: logging.Logger = logging.getLogger(name="camera")


class Camera:
    def __init__(self,
                 config: Configuration,
                 loop,
                 camera_task_queue_async: asyncio.Queue,
                 message_task_queue: queue.Queue
                 ) -> None:
        self.logger: logging.Logger = logging.getLogger(name="Camera")
        self.config: Configuration = config
        self.loop = loop
        self.camera_task_queue_async: asyncio.Queue = camera_task_queue_async
        self.message_task_queue = message_task_queue
        self.logger.debug(msg="initialize camera class instance")
        self.running: bool = True

    async def start(self) -> None:
        logger.debug(msg="thread camera start")

        if (self.config.blink_enabled):
            self.logger.debug("start blink session")
            self.session = aiohttp.ClientSession()
            self.logger.debug("add session to blink")
            self.blink = Blink(session=self.session, refresh_rate=3)
            await self.read_blink_config()
            await self.blink.start()

        logger.info("camera now start endless loop")
        while self.running:
            try:
                self.logger.debug("camera_task_queue_async get task")
                task = await self.camera_task_queue_async.get()

                if task is None:  # Exit signal
                    self.logger.info("no task")
                    break
                self.logger.info(f"asyncthread received task: {task}")

                if isinstance(task, Camera_Task):
                    self.logger.debug(f"Async Processing Camera_Task with data: {task}")
                    if task.photo:
                        self.logger.info(f"processing task.photo: {task.photo}")
                        await self.choose_cam(task)


                    elif task.picam_photo:
                        self.logger.info(f"processing task.picam_photo: {task.picam_photo}")
                        self._picam_foto_helper(task)

                    elif task.blink_photo:
                        self.logger.info(f"processing task.blink_photo: {task.blink_photo}")
                        await self._blink_foto_helper(task)

                    elif task.blink_mfa:
                        self.logger.info(f"processing task.blink_mfa: {task.blink_mfa}")
                        result = await self.add_2fa_blink_token(task)
                        if result:
                            result = await self.save_blink_config()
                            if result:
                                self.message_task_queue.put(Message_Task(reply=True,
                                                                         chat_id=task.chat_id,
                                                                         message=task.message,
                                                                         data_text="blink MFA added"))
                            else:
                                self.message_task_queue.put(Message_Task(reply=True,
                                                                         chat_id=task.chat_id,
                                                                         message=task.message,
                                                                         data_text="an error occured during blink MFA "
                                                                                   "processing"))
                        else:
                            self.message_task_queue.put(Message_Task(reply=True,
                                                                     chat_id=task.chat_id,
                                                                     message=task.message,
                                                                     data_text="an error occured during blink MFA "
                                                                               "processing"))
            except Exception as err:
                self.logger.error("Error: {0}".format(err))
                pass

        await self.session.close()


    async def choose_cam(self, task: Camera_Task):

        self.logger.debug("choose camera")
        # check if daylight detection is enabled or not take default
        if (self.config.enable_detect_daylight):
            self.logger.debug("daylight detection is enabled")

            # detect daylight = true or night = false
            if self.detect_daylight():
                self.logger.info("daylight detected")

                if not self.config.blink_night_vision:
                    self.logger.debug("blink night_vision is disabled")
                    result = await self._blink_foto_helper(task)
                    return await self._check_blink_result(task, result)

                if not self.config.picam_night_vision:
                    self.logger.debug("picam night_vision is disabled")
                    result = self._picam_foto_helper(task)
                    return self._check_picam_result(task, result)

            else:
                self.logger.info("night detected is enabled")

                if self.config.blink_night_vision:
                    self.logger.debug("blink night_vision is enabled")
                    result = await self._blink_foto_helper(task)
                    return await self._check_blink_result(task, result)

                if self.config.picam_night_vision:
                    self.logger.debug("picam night_vision is enabled")
                    result = self._picam_foto_helper(task)
                    return self._check_picam_result(task, result)

        else:
            # use default camera
            if self.config.default_camera_type == DefaultCam.BLINK:
                self.logger.debug("blink as default cam choosen")
                result = await self._blink_foto_helper(task)
                return await self._check_blink_result(task, result)

            if self.config.default_camera_type == DefaultCam.PICAM:
                self.logger.debug("picam as default cam is choosen")
                result = self._picam_foto_helper(task)
                return self._check_picam_result(task, result)

    def _picam_foto_helper(self, task: Camera_Task) -> bool:

        if (self.config.picam_enabled):
            self.logger.debug("_picam_foto_helper - picam enabled")
            result = self.picam_request_take_foto()
            if result:
                self.logger.debug("picam snapshot success")
                result = self.picam_request_download_foto()
                if result:
                    self.logger.debug("picam snapshot download success")
                    self.put_msg_queue_photo(task)
                else:
                    self.logger.error("picam snapshot download error")
                    self.put_msg_queue_error(task, "an error occured during PiCam foto download ")
            else:
                self.logger.error("picam snapshot error")
                self.put_msg_queue_error(task, "an error occured during PiCam snapshot")
        else:
            self.logger.info("_picam_foto_helper - picam disabled")
            return False
        return result

    async def _blink_foto_helper(self, task: Camera_Task) -> bool:
        if (self.config.blink_enabled):
            self.logger.debug("_blink_foto_helper - blink enabled")
            result = await self.blink_snapshot()
            if result:
                self.logger.debug("blink snapshot success")
                self.put_msg_queue_photo(task)
            else:
                self.logger.error("blink snapshot error detected")
                self.put_msg_queue_error(task, "an error occured during pocessing Blink foto task")
        else:
            self.logger.info("_blink_foto_helper - blink disabled")
            return False
        return result

    def _check_picam_result(self, task: Camera_Task, result: bool) -> bool:
        self.logger.debug("picam _check_picam_result")
        if not result:
            self.logger.debug("_check_picam_result FALSE")
            if (self.config.blink_enabled):
                self.logger.error("_check_picam_result - second try now with blink")
                return self._blink_foto_helper(task)
            else:
                self.logger.error("_check_picam_result - blink not enabled for second try")
        return result

    async def _check_blink_result(self, task: Camera_Task, result: bool) -> bool:
        self.logger.debug("blink _check_blink_result")
        if not result:
            self.logger.debug("blink _check_blink_result FALSE")
            if (self.config.picam_enabled):
                self.logger.error("_check_blink_result - second try now with picam")
                return self._picam_foto_helper(task)
            else:
                self.logger.error("_check_blink_result - picam not enabled for second try")
        return result

    def put_msg_queue_photo(self, task: Camera_Task):
        if task.reply:
            self.message_task_queue.put(Message_Task(photo=True,
                                                     filename=self.config.photo_image_path,
                                                     chat_id=task.chat_id,
                                                     message=task.message))
        else:
            self.message_task_queue.put(Message_Task(photo=True,
                                                     filename=self.config.photo_image_path,
                                                     chat_id=task.chat_id))

    def put_msg_queue_error(self, task: Camera_Task, message: str):
        if task.reply:
            self.message_task_queue.put(Message_Task(reply=True,
                                                     data_text=message,
                                                     chat_id=task.chat_id,
                                                     message=task.message))
        else:
            self.message_task_queue.put(Message_Task(send=True,
                                                           data_text=message,
                                                           chat_id=task.chat_id))

    def detect_daylight(self) -> bool:
        """
        Detects daylight and returns boolean
        :return: boolean
        """
        loc = LocationInfo(name="Berlin", region="Germany", timezone="Europe/Berlin")
        time_now: datetime = datetime.now(tz=timezone.utc)
        s: dict[str, datetime] = sun(observer=loc.observer, date=time_now, tzinfo=loc.timezone)
        daylight: bool = (s['sunrise'] <= time_now <= (s['sunset']))
        self.logger.info(msg=f"Is daylight detected: {daylight}")
        return daylight

    async def blink_snapshot(self) -> bool:
        """Creates a new blink cam snapshot and downloads it.
        """
        self.logger.info(
            msg="i'll take a snapshot from blink cam {0} and store it here {1}".format(
                self.config.blink_name, self.config.photo_image_path))
        try:
            await self.blink.refresh(force=True)
            self.logger.debug("create a camera instance")
            camera = self.blink.cameras[self.config.blink_name]
        except Exception as err:
            self.logger.error("Error: {0}".format(err))
            return False

        logger.debug("take a snpshot")
        try:
            await camera.snap_picture()  # Take a new picture with the camera
        except Exception as err:
            self.logger.error("Error: {0}".format(err))
            self.logger.error("Error: {0}".format(err.with_traceback()))
            self.logger.error("Error: {0}".format(err.args))
            return False

        self.logger.debug("refresh blink server info")
        time.sleep(2)  # wait for blink class instane refresh invterval to be done
        await self.blink.refresh(force=True)  # refesh Server info
        if os.path.exists(self.config.photo_image_path):
            self.logger.debug("a file already exists and will be deteleted before hand")
            os.remove(self.config.photo_image_path)
        self.logger.info("saving blink foto")
        await camera.image_to_file(self.config.photo_image_path)
        return True

    async def read_blink_config(self):
        if os.path.exists(self.config.blink_config_file):
            self.blink.auth = Auth(await json_load(self.config.blink_config_file), no_prompt=True, session=self.session)
            self.logger.info("blink aut with file done")
            authentication_success = True
        else:
            self.logger.info(
                "no blink_config.json found - 2FA " + "authentication token required"
            )
            self.blink.auth = Auth(
                {"username": self.config.blink_username, "password": self.config.blink_password}, no_prompt=True,
                session=self.session
            )
            authentication_success = None

    async def save_blink_config(self) -> bool:
        """Saves an existing blink session into a config file.

        This save a bink session for reuse on device with already
        authenticated token into a config file.

        :return: success True
        :rtype: boolean
        """
        self.logger.info("saving blink authenticated session infos into config file")
        await self.blink.save(self.config.blink_config_file)
        return True

    async def add_2fa_blink_token(self, task: Camera_Task) -> bool:
        """Adds a required 2FA token to blink session.

        :return: success True
        :rtype: boolean
        """
        self.logger.debug("add a 2FA token for authentication")
        await self.blink.auth.send_auth_key(self.blink, task.blink_mfa)
        self.logger.debug("verify 2FA token")
        # ToDo implement  exception handling with return false
        await self.blink.setup_post_verify()
        self.logger.info("added 2FA token " + task.blink_mfa)
        return True

    def picam_request_take_foto(self) -> bool:
        """Take a photo from PiCam

        This creates a new snapshot via PiCam REST-API with a
        POST request.

        :return: True if http request status code == 200 else False
        :rtype: bool
        """
        self.logger.info(msg="take a PiCam snapshot")
        self.logger.debug(msg=f"post url={self.config.picam_url}")
        payload: dict[str, any] = {
            "rotation": self.config.picam_rotation,
            "width": self.config.picam_image_width,
            "filename": self.config.picam_image_filename,
            "hight": self.config.picam_image_hight,
            "exposure": self.config.picam_exposure,
            "iso": self.config.picam_iso,
        }
        self.logger.debug(msg=payload)
        headers: dict[str, str] = {"content-type": "application/json"}
        self.logger.debug(msg=headers)
        response: requests.Response = requests.post(url=self.config.picam_url, data=json.dumps(obj=payload),
                                                    headers=headers)
        self.logger.debug(msg="make a snapshot ended with http status {}".format(response.status_code))

        return True if response.status_code == 200 else False

    def picam_request_download_foto(self) -> bool:
        """Downloads a Photo via GET request from PiCAM REST-API

        :return: http request status code
        :rtype: int
        """
        self.logger.info(msg="downloading PiCam foto")
        if os.path.exists(path=self.config.photo_image_path):
            logger.debug(msg="deleting already existing file before hand")
            os.remove(path=self.config.photo_image_path)

        with open(self.config.photo_image_path, "wb") as file:
            response: requests.Response = requests.get(
                url=self.config.picam_url + "?filename=" + self.config.photo_image_path)
            file.write(response.content)
        self.logger.debug(msg="downloading foto ended with status {}".format(response.status_code))
        self.logger.debug(msg="end downloading foto")
        return True if response.status_code == 200 else False
