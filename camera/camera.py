from __future__ import annotations

import asyncio
import certifi
import logging
import os
from pathlib import Path
import queue
import ssl
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo
import aiohttp
import requests

from PIL import Image, ImageEnhance
from astral import LocationInfo
from astral.sun import sun
from blinkpy.auth import (
    Auth,
    BlinkBadResponse,
    UnauthorizedError,
    BlinkTwoFARequiredError,
    TokenRefreshFailed,
    LoginError,
)
from blinkpy.blinkpy import Blink, BlinkSetupError
from blinkpy.helpers.util import json_load

from config.config_util import Configuration, DefaultCam
from config.data_class import Camera_Task, Message_Task

logger: logging.Logger = logging.getLogger(name="camera")


class Camera:
    def __init__(
        self,
        config: Configuration,
        loop,
        camera_task_queue_async: asyncio.Queue,
        message_task_queue: queue.Queue,
    ) -> None:
        """
        Initializes a new instance of the Camera class.

        Args:
            config (Configuration): The configuration object for the camera.
            loop: The event loop for the camera.
            camera_task_queue_async (asyncio.Queue): The asynchronous queue for camera tasks.
            message_task_queue (queue.Queue): The queue for message tasks.

        Returns:
            None

        Initializes the logger with the name "Camera", sets the configuration object, event loop,
        asynchronous queue for camera tasks, and message task queue. Logs a debug message indicating
        the initialization of the camera class instance. Sets the running flag to True.
        """
        self.logger: logging.Logger = logging.getLogger(name="Camera")
        self.config: Configuration = config
        self.loop = loop
        self.camera_task_queue_async: asyncio.Queue = camera_task_queue_async
        self.message_task_queue = message_task_queue
        self.logger.debug(msg="initialize camera class instance")
        self.running: bool = True
        self.restart: bool = False
        self.session: aiohttp.ClientSession | None = None
        self.blink: Blink | None = None
        self.picam_photo_id: str | None = None

    def __create_blink_session(self) -> aiohttp.ClientSession:
        """
        Create an aiohttp session with an explicit CA bundle.

        PyInstaller binaries on macOS may not reliably inherit system CA paths,
        so we bind aiohttp directly to certifi's trust store.
        """
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        return aiohttp.ClientSession(connector=connector)

    async def start(self) -> None:
        """
        Initializes the camera, starts a blink session if enabled, and processes
        various camera tasks asynchronously.
        """
        logger.debug(msg="thread camera start")
        restart_requested = False

        if self.config.blink_enabled:
            self.logger.debug("start blink session")
            self.session = self.__create_blink_session()
            self.logger.debug("add session to blink")
            self.blink = Blink(session=self.session, refresh_rate=3)
            await self.__read_blink_config()
            try:
                self.logger.info("start blink")
                await self.blink.start()
            except BlinkTwoFARequiredError:
                self.logger.info("BlinkTwoFARequiredError")
                self.message_task_queue.put(
                    Message_Task(
                        send=True,
                        chat_id=self.config.telegram_chat_nr,
                        data_text="BlinkTwoFARequiredError - please provide 2FA token from Blink via command /blink_auth <token>",
                    )
                )
            except BlinkSetupError as e:
                self.logger.error(f"BlinkSetupError: {e}")
                self.message_task_queue.put(
                    Message_Task(
                        send=True,
                        chat_id=self.config.telegram_chat_nr,
                        data_text="BlinkSetupError - an error occured during Blink setup - check logs",
                    )
                )
            except TokenRefreshFailed as e:
                self.logger.error(f"TokenRefreshFailed: {e}")
                self.message_task_queue.put(
                    Message_Task(
                        send=True,
                        chat_id=self.config.telegram_chat_nr,
                        data_text="An Blink TokenRefreshFailed error occured - check logs",
                    )
                )
            except LoginError as e:
                self.logger.error(f"Blink LoginError: {e}")
                self.message_task_queue.put(
                    Message_Task(
                        send=True,
                        chat_id=self.config.telegram_chat_nr,
                        data_text="An LoginError occured during Blink start - check logs",
                    )
                )
            except BlinkBadResponse as e:
                self.logger.error(f"Unexpected BlinkBadResponse occured: {e}")
                self.message_task_queue.put(
                    Message_Task(
                        send=True,
                        chat_id=self.config.telegram_chat_nr,
                        data_text="Unexpected BlinkBadResponse occured - check logs",
                    )
                )
            except UnauthorizedError as e:
                self.logger.error(
                    f"An authorization UnauthorizedError occured at  Blink start: {e}"
                )
                self.message_task_queue.put(
                    Message_Task(
                        send=True,
                        chat_id=self.config.telegram_chat_nr,
                        data_text="An authorization UnauthorizedError occured at  Blink start",
                    )
                )
                blink_file_path = Path(self.config.blink_config_file)
                if blink_file_path.exists():
                    blink_file_path.unlink()
                    self.logger.info(
                        f"{self.config.blink_config_file} deleted because authentication error."
                    )
                else:
                    self.logger.warning(
                        f"want {self.config.blink_config_file} to delete but was not existing"
                    )
                    self.message_task_queue.put(
                        Message_Task(
                            send=True,
                            chat_id=self.config.telegram_chat_nr,
                            data_text=f"want {blink_file_path} to delete but was not existing",
                        )
                    )
                # restart
                if not self.restart:
                    self.restart = True
                    restart_requested = True

        if restart_requested:
            await self.__close_session()
            await self.start()
            return

        logger.info("camera now start endless loop")
        while self.running:
            try:
                self.logger.debug("camera_task_queue_async get task")
                task = await asyncio.wait_for(self.camera_task_queue_async.get(), timeout=0.5)

                if task is None:  # Exit signal
                    self.logger.info("no task")
                    break
                self.logger.info(f"asyncthread received task: {task}")

                if isinstance(task, Camera_Task):
                    self.logger.debug(f"Async Processing Camera_Task with data: {task}")
                    if task.photo:
                        self.logger.info(f"processing task.photo: {task.photo}")
                        await self.__choose_cam(task)

                    elif task.picam_photo:
                        self.logger.info(
                            f"processing task.picam_photo: {task.picam_photo}"
                        )
                        await self.__picam_foto_helper(task)

                    elif task.blink_photo:
                        self.logger.info(
                            f"processing task.blink_photo: {task.blink_photo}"
                        )
                        await self.__blink_foto_helper(task)

                    elif task.blink_mfa:
                        self.logger.info(f"processing task.blink_mfa: {task.blink_mfa}")

                        result = await self.__add_2fa_blink_token(task)
                        if result:
                            result = await self.__save_blink_config()
                            if result:
                                self.message_task_queue.put(
                                    Message_Task(
                                        reply=True,
                                        chat_id=task.chat_id,
                                        message=task.message,
                                        data_text="blink MFA added",
                                    )
                                )
                            else:
                                self.message_task_queue.put(
                                    Message_Task(
                                        reply=True,
                                        chat_id=task.chat_id,
                                        message=task.message,
                                        data_text="an error occured during blink MFA "
                                        "processing",
                                    )
                                )
                        else:
                            self.message_task_queue.put(
                                Message_Task(
                                    reply=True,
                                    chat_id=task.chat_id,
                                    message=task.message,
                                    data_text="an error occured during blink MFA "
                                    "processing",
                                )
                            )
            except asyncio.TimeoutError:
                continue
            except Exception as err:
                self.logger.error("Error: {0}".format(err))
                pass

        await self.__close_session()

    async def __choose_cam(self, task: Camera_Task):
        """
        Asynchronously chooses a camera based on various conditions such as
        daylight detection, night vision, and default camera type.
        Decision is:
        - daylight detection enabled:
            - daylight takes default_camera_type
            - night: takes night vision enabled cam, if two precedence is blink over picam
        - daylight detection disabled:
            - takes default_camera_type

        Args:
            self: The Camera object.
            task (Camera_Task): The task containing information for camera selection.

        Returns:
            The result of the camera selection process.
        """
        self.logger.debug("choose camera")
        # check if daylight detection is enabled or not take default
        if self.config.enable_detect_daylight:
            self.logger.debug("daylight detection is enabled")

            # detect daylight = true or night = false
            if self.__detect_daylight():
                self.logger.info("daylight detected")

                if self.config.default_camera_type == DefaultCam.BLINK:
                    self.logger.debug("blink night_vision is disabled")
                    result = await self.__blink_foto_helper(task)
                    return await self.__check_blink_result(task, result)

                if self.config.default_camera_type == DefaultCam.PICAM:
                    self.logger.debug("picam night_vision is disabled")
                    result = await self.__picam_foto_helper(task)
                    return await self.__check_picam_result(task, result)

            else:
                self.logger.info("night detected is enabled")

                # ToDo: improve here if two are enabled for night vision
                # ToDo: further extended unit tests required here
                if self.config.blink_night_vision:
                    self.logger.debug("blink night_vision is enabled")
                    result = await self.__blink_foto_helper(task)
                    return await self.__check_blink_result(task, result)

                if (
                    self.config.picam_night_vision
                    or self.config.picam_image_brightening
                ):
                    self.logger.debug(
                        f"picam night_vision is {self.config.picam_night_vision}"
                    )
                    self.logger.debug(
                        f"picam image_brightening is {self.config.picam_image_brightening}"
                    )
                    result = await self.__picam_foto_helper(task)
                    return await self.__check_picam_result(task, result)

        else:
            if self.config.default_camera_type == DefaultCam.BLINK:
                self.logger.debug("blink as default cam choosen")
                result = await self.__blink_foto_helper(task)
                return await self.__check_blink_result(task, result)

            if self.config.default_camera_type == DefaultCam.PICAM:
                self.logger.debug("picam as default cam is choosen")
                result = await self.__picam_foto_helper(task)
                return await self.__check_picam_result(task, result)

    async def __picam_foto_helper(self, task: Camera_Task) -> bool:
        """
        A helper function for the PiCam to take and download a photo, log
        success and errors, and manage the message queue.

        Parameters:
            task (Camera_Task): The task object associated with the photo-taking process.

        Returns:
            bool: True if the photo was successfully taken and downloaded, False otherwise.
        """
        if self.config.picam_enabled:
            self.logger.debug("_picam_foto_helper - picam enabled")
            result = self.__picam_request_take_foto()
            if result:
                self.logger.debug("picam snapshot success")
                result = self.__picam_request_download_foto()
                if result:
                    self.logger.debug("picam snapshot download success")
                    self.__put_msg_queue_photo(task)
                else:
                    self.logger.error("picam snapshot download error")
                    self.__put_msg_queue_error(
                        task, "an error occured during PiCam foto download "
                    )
            else:
                self.logger.error("picam snapshot error")
                self.__put_msg_queue_error(task, "an error occured during PiCam snapshot")
        else:
            self.logger.info("_picam_foto_helper - picam disabled")
            return False
        return result

    async def __blink_foto_helper(self, task: Camera_Task) -> bool:
        """
        Asynchronously takes a photo using the Blink camera if enabled in the configuration.

        Args:
            task (Camera_Task): The camera task containing information about the task.

        Returns:
            bool: True if the photo was successfully taken and processed, False otherwise.

        This function checks if the Blink camera is enabled in the configuration. If it is,
        it takes a photo using the Blink camera and processes the result. If the photo was
        successfully taken, it puts the photo in the message queue. If the photo was not taken
        successfully, it puts an error message in the message queue. If the Blink camera is not
        enabled, it logs a message and returns False.
        """
        if self.config.blink_enabled:
            self.logger.debug("_blink_foto_helper - blink enabled")
            result = await self.__blink_snapshot()
            if result:
                self.logger.debug("blink snapshot success")
                self.__put_msg_queue_photo(task)
            else:
                self.logger.error("blink snapshot error detected")
                self.__put_msg_queue_error(
                    task, "an error occured during pocessing Blink foto task"
                )
        else:
            self.logger.info("_blink_foto_helper - blink disabled")
            return False
        return result

    async def __check_picam_result(self, task: Camera_Task, result: bool) -> bool:
        """
        Check the result of the picam function.

        Args:
            task (Camera_Task): The task to be checked.
            result (bool): The result of the picam function.

        Returns:
            bool: The result of the picam function.

        This function checks the result of the picam function. If the result is False,
        it logs a debug message.
        If the blink camera is enabled in the configuration, it calls the _blink_foto_helper
        function with the task.
        If the blink camera is not enabled, it logs an error message.
        """
        self.logger.debug("picam _check_picam_result")
        if not result:
            self.logger.debug("_check_picam_result FALSE")
            if self.config.blink_enabled:
                self.logger.error("_check_picam_result - second try now with blink")
                return await self.__blink_foto_helper(task)
            else:
                self.logger.error(
                    "_check_picam_result - blink not enabled for second try"
                )
        return result

    async def __check_blink_result(self, task: Camera_Task, result: bool) -> bool:
        """
        Check the result of the picam function.

        Args:
            task (Camera_Task): The task to be checked.
            result (bool): The result of the picam function.

        Returns:
            bool: The result of the picam function.

        This function checks the result of the picam function. If the result is False,
        it logs a debug message.
        If the blink camera is enabled in the configuration, it calls the _picam_foto_helper
        function with the task.
        If the blink camera is not enabled, it logs an error message.
        """
        self.logger.debug("blink _check_blink_result")
        if not result:
            self.logger.debug("blink _check_blink_result FALSE")
            if self.config.picam_enabled:
                self.logger.error("_check_blink_result - second try now with picam")
                return await self.__picam_foto_helper(task)
            else:
                self.logger.error(
                    "_check_blink_result - picam not enabled for second try"
                )
        return result

    def __put_msg_queue_photo(self, task: Camera_Task):
        """
        Puts a message queue photo based on the provided task.

        Args:
            task (Camera_Task): The task to be processed.

        Returns:
            None
        """
        if task.reply:
            self.message_task_queue.put(
                Message_Task(
                    photo=True,
                    filename=self.config.photo_image_path,
                    chat_id=task.chat_id,
                    message=task.message,
                )
            )
        else:
            self.message_task_queue.put(
                Message_Task(
                    photo=True,
                    filename=self.config.photo_image_path,
                    chat_id=task.chat_id,
                )
            )

    def __put_msg_queue_error(self, task: Camera_Task, message: str):
        """
        Puts a message queue error based on the provided task and message.

        Args:
            task (Camera_Task): The task to be processed.
            message (str): The error message to be added to the queue.

        Returns:
            None
        """
        if task.reply:
            self.message_task_queue.put(
                Message_Task(
                    reply=True,
                    data_text=message,
                    chat_id=task.chat_id,
                    message=task.message,
                )
            )
        else:
            self.message_task_queue.put(
                Message_Task(send=True, data_text=message, chat_id=task.chat_id)
            )

    def __detect_daylight(self) -> bool:
        """
        Detects whether it is currently daylight based on sunrise and sunset times.

        The method uses either the configured coordinates (latitude and longitude)
        or the configured country to calculate sun times.

        Returns:
            bool: True if it is daylight (between sunrise and sunset),
                  False if it is dark
                  Incase of error True is returned as daylight
        """
        try:
            local_tz = ZoneInfo(self.config.timezone)
            local_date = datetime.now(local_tz)
            if self.config.lat is not None and self.config.lon is not None:
                self.logger.debug("using coordinates for daylight detection")
                location = LocationInfo(
                    name=self.config.city,
                    region=self.config.country,
                    latitude=self.config.lat,
                    longitude=self.config.lon,
                    timezone=self.config.timezone,
                )
                self.logger.debug(f"location: {location}")
                s = sun(location.observer, date=local_date)
            elif self.config.country is not None:
                self.logger.debug("using country - city for daylight detection")
                location = LocationInfo(name=self.config.country)
                s = sun(location.observer, date=local_date)
            else:
                raise ValueError("No valid country data provided")

            self.logger.debug(f"Sunrise: {s['sunrise']}, Sunset: {s['sunset']}")
            time_now = datetime.now(
                tz=ZoneInfo(self.config.timezone)
            )  # Konvertiere String zu ZoneInfo
            daylight: bool = s["sunrise"] <= time_now <= s["sunset"]
            self.logger.info(msg=f"Is daylight detected: {daylight}")
            return daylight
        except ValueError as e:
            self.logger.error("Invalid Location data: " + str(e))
            return True
        except Exception as e:
            self.logger.error("Error in daylight calculation: " + str(e))
            return True

    async def __blink_snapshot(self) -> bool:
        """
        Asynchronously takes a snapshot from a Blink camera and saves it to a specified file path.
        If detect_daylight is night and when image_brightning is enabled, the image will be adjusted.

        Returns:
            bool: True if the snapshot was successfully taken and saved, False otherwise.
        """
        self.logger.info(
            msg="i'll take a snapshot from blink cam {0} and store it here {1}".format(
                self.config.blink_name, self.config.photo_image_path
            )
        )
        try:
            # await self.blink.refresh(force=True)
            self.logger.debug("create a camera instance")
            camera = self.blink.cameras[self.config.blink_name]
            logger.debug("take a snpshot")
            await camera.snap_picture()  # Take a new picture with the camera
            self.logger.debug("refresh blink server info")
            await asyncio.sleep(delay=2)
            # time.sleep(2)  # wait for blink class instance refresh interval to be done
            refresh_result: bool = await self.blink.refresh(
                force=True
            )  # refresh Server info
            if not refresh_result:
                self.logger.error("an error occured during blink refresh")
                return False
            if os.path.exists(self.config.photo_image_path):
                self.logger.debug(
                    "a file already exists and will be deleted before hand"
                )
                os.remove(self.config.photo_image_path)
            else:
                os.makedirs(
                    os.path.dirname(self.config.photo_image_path), exist_ok=True
                )
                self.logger.debug("directory created for the photo image path")
            self.logger.info("saving blink foto")
            await camera.image_to_file(self.config.photo_image_path)
            if not self.__detect_daylight() and self.config.blink_image_brightening:
                self.__adjust_image()
        # ToDo: further exception handlinhg required here  / improvement
        except Exception as err:
            self.logger.error("Error: {0}".format(err))
            self.logger.error("Error args: {0}".format(err.args))
            return False

        return True

    async def __read_blink_config(self):
        """
        Asynchronously reads the Blink configuration file and authenticates with Blink.

        This function checks if the Blink configuration file exists. If it does, it loads
        the configuration file using the `json_load` function, creates an `Auth` object
        with the loaded configuration, sets the `auth` attribute of the `blink` object to
        the created `Auth` object, logs a message indicating that the authentication was
        done using the file, and sets the `authentication_success` variable to `True`.

        If the Blink configuration file does not exist, it logs a message indicating that
        the file was not found and that a 2FA authentication token is required. It creates
        an `Auth` object with the provided Blink username and password, sets the `auth`
        attribute of the `blink` object to the created `Auth` object, and sets the
        `authentication_success` variable to `None`.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        if os.path.exists(self.config.blink_config_file):
            self.blink.auth = Auth(
                await json_load(self.config.blink_config_file),
                no_prompt=True,
                session=self.session,
            )
            self.logger.info("blink aut with file done")
            # authentication_success = True
        else:
            self.logger.info(
                "no blink_config.json found - 2FA " + "authentication token required"
            )
            self.blink.auth = Auth(
                {
                    "username": self.config.blink_username,
                    "password": self.config.blink_password,
                },
                no_prompt=True,
                session=self.session,
            )
            # authentication_success = None

    async def __close_session(self) -> None:
        if self.session is None:
            return
        await self.session.close()
        self.session = None

    async def __save_blink_config(self) -> bool:
        """
        Saves the authenticated session information of the Blink service into a config file.

        This function saves the authenticated session information of the Blink service into a config file.
        It logs a message indicating that the session information is being saved.
        Then it calls the `save` method of the `blink` object, passing the `blink_config_file` attribute
        of the `config` object as the file path.

        Parameters:
            self (object): The instance of the class.

        Returns:
            bool: True if the session information is successfully saved.
        """
        self.logger.info("saving blink authenticated session infos into config file")
        await self.blink.save(self.config.blink_config_file)
        return True

    async def __add_2fa_blink_token(self, task: Camera_Task) -> bool:
        """
        Adds a required 2FA token to blink session.

        Parameters:
            self (object): The instance of the class.
            task (Camera_Task): The task containing the 2FA token information.

        Returns:
            bool: True if the token is successfully added.
        """
        self.logger.debug("add a 2FA token for authentication")
        await self.blink.send_2fa_code(task.blink_mfa)
        self.logger.debug("verify 2FA token")
        result = await self.blink.setup_post_verify()
        if result:
            self.logger.info("added 2FA token " + task.blink_mfa)
            return True
        else:
            self.logger.error("an error occured during verifying 2FA token")
            return False

    def __picam_request_take_foto(self) -> bool:
        """
        A function to request taking a photo using PiCam, sending a POST request with specific parameters, and logging the process.

        :return: True if the HTTP request status code is 200, otherwise False
        :rtype: bool
        """
        self.logger.info(msg="take a PiCam snapshot")
        picam_url = self.__get_picam_api_url()
        self.logger.debug(msg=f"post url={picam_url}")
        self.picam_photo_id = None
        payload: dict[str, int | str] = {
            "rotation": self.config.picam_rotation,
            "width": self.config.picam_image_width,
            "height": self.config.picam_image_hight,
            "exposure": self.config.picam_exposure,
            "iso": self.config.picam_iso,
        }
        self.logger.debug(msg=payload)
        headers: dict[str, str] = {"content-type": "application/json"}
        self.logger.debug(msg=headers)
        try:
            response: requests.Response = requests.post(
                url=picam_url, json=payload, headers=headers
            )
            response.raise_for_status()
            response_json = response.json()
            self.picam_photo_id = response_json.get("photo_id")
            if not self.picam_photo_id:
                self.logger.error("PiCam response does not contain a photo_id")
                return False
            self.logger.debug(
                msg="make a snapshot ended with http status {}".format(
                    response.status_code
                )
            )
            return True if response.status_code == 200 else False

        except Exception as e:
            self.logger.error("Exception: {}".format(e))
        return False

    def __picam_request_download_foto(self) -> bool:
        """
        Downloads a photo from the PiCam REST-API.

        This function sends a GET request to the PiCam API to download a photo.
        The photo is saved to the file specified in the `photo_image_path`
        configuration.
        If detect_daylight night and when image_brightning is enabled, the image will be adjusted.

        Returns:
            bool: True if the HTTP request status code is 200, otherwise False.
        """
        self.logger.info(msg="downloading PiCam foto")
        if not self.picam_photo_id:
            self.logger.error("No PiCam photo_id available for download")
            return False
        picam_url = self.__get_picam_api_url()
        if os.path.exists(path=self.config.photo_image_path):
            logger.debug(msg="deleting already existing file before hand")
            os.remove(path=self.config.photo_image_path)
        else:
            os.makedirs(os.path.dirname(self.config.photo_image_path), exist_ok=True)

        try:
            with open(self.config.photo_image_path, "wb") as file:
                response: requests.Response = requests.get(
                    url=picam_url,
                    params={"photo_id": self.picam_photo_id},
                )
                response.raise_for_status()
                file.write(response.content)
                if not self.__detect_daylight() and self.config.picam_image_brightening:
                    self.__adjust_image()

            self.logger.debug(
                msg="downloading foto ended with status {}".format(response.status_code)
            )
            self.logger.debug(msg="end downloading foto")
            return True if response.status_code == 200 else False

        except Exception as e:
            self.logger.error("Error: {0}".format(e))
            self.logger.error("Error args: {0}".format(e.args))
        return False

    def __get_picam_api_url(self) -> str:
        """
        Returns the PiCam API endpoint without legacy query parameters.

        Older configurations used values like `/foto/?filename=foto.jpg`.
        The current API requires a clean `/foto/` endpoint plus a `photo_id`
        query parameter added by the client during download.
        """
        picam_url = self.config.picam_url.strip()
        url_parts = urlsplit(picam_url)
        if url_parts.query or url_parts.fragment:
            self.logger.warning(
                "PiCam URL contains legacy query or fragment data; stripping it: %s",
                picam_url,
            )
        return urlunsplit(
            (url_parts.scheme, url_parts.netloc, url_parts.path, "", "")
        )

    def __adjust_image(self) -> bool:
        """
        Adjusts brightness and contrast of the stored photo based on the
        configuration values.

        Returns:
            bool: True if adjustment was successful, False on errors
        """
        try:
            self.logger.info("start image brightness adjustement")

            if not os.path.exists(self.config.photo_image_path):
                self.logger.error(
                    f"Image file not found: {self.config.photo_image_path}"
                )
                return False

            image = Image.open(self.config.photo_image_path)

            # brightness adjustement (1.0 is normal, <1 darker, >1 lighter)
            brightness = getattr(
                self.config,
                "brightness_enhancer",
                getattr(self.config, "image_brightness", None),
            )
            if brightness is not None:
                brightness_enhancer = ImageEnhance.Brightness(image)
                image = brightness_enhancer.enhance(brightness)
                self.logger.debug(f"brightness adjusted to {brightness}")

            contrast = getattr(
                self.config,
                "contrast_enhancer",
                getattr(self.config, "image_contrast", None),
            )
            if contrast is not None:
                contrast_enhancer = ImageEnhance.Contrast(image)
                image = contrast_enhancer.enhance(contrast)
                self.logger.debug(f"contrast adjusted to {contrast}")

            image.save(self.config.photo_image_path)
            self.logger.debug("imgae adjustment done")
            return True

        except Exception as err:
            self.logger.error(f"Error during image brightness adjustement: {err}")
            return False
